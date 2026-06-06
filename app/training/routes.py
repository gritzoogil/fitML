from flask import render_template, request, jsonify, session, redirect
from app.training import training_bp
from db.database import execute_query
from app.model.progressive_overload import (
    predict_next_session, compute_fatigue_per_set, compute_f_cap,
    average_1rm, mifflin_st_jeor, estimate_tdee, adaptive_tdee, classify_diet
)
from datetime import date, timedelta, datetime
from functools import wraps
import uuid

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated

@training_bp.route('/')
@login_required
def index():
    user_id = session['user_id']

    # Get current week's Monday
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Check if weekly check-in exists for this week
    checkin = execute_query("""
        SELECT * FROM weekly_checkins
        WHERE user_id = %s AND week_start = %s
    """, (user_id, week_start), fetch='one')

    # Calculate F_cap from check-in or use defaults
    if checkin:
        f_cap = compute_f_cap(
            weight_lbs=163.0,
            sleep_hours=float(checkin['avg_sleep_hours']),
            diet=checkin['diet_status'],
            stress=checkin['stress_level'],
            genetics=checkin['genetics']
        )
    else:
        f_cap = None  # triggers modal

    # Get weekly fatigue
    weekly_fatigue = execute_query("""
        SELECT COALESCE(SUM(total_fatigue), 0) as total
        FROM exercise_sets
        WHERE user_id = %s AND created_at >= %s
    """, (user_id, week_start), fetch='one')

    f_total = float(weekly_fatigue['total']) if weekly_fatigue else 0
    net_balance = round(f_cap - f_total, 2) if f_cap else None

    # Get last 5 sessions
    sessions = execute_query("""
        SELECT id, session_date, session_type, notes
        FROM training_sessions
        WHERE user_id = %s
        ORDER BY session_date DESC
        LIMIT 5
    """, (user_id,), fetch='all')

    return render_template('training/index.html',
        sessions=sessions,
        f_cap=f_cap,
        f_total=round(f_total, 2),
        net_balance=net_balance,
        show_checkin_modal=checkin is None,
        checkin=checkin,
        today=today
    )

@training_bp.route('/session/new', methods=['GET', 'POST'])
@login_required
def new_session():
    if request.method == 'POST':
        user_id = session['user_id']
        data = request.get_json()

        # Create session
        session_id = str(uuid.uuid4())
        execute_query("""
            INSERT INTO training_sessions (id, user_id, session_date, session_type, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, user_id, data['date'], data['session_type'], data.get('notes', '')))

        # Save each exercise set
        for ex in data.get('exercises', []):
            fatigue = compute_fatigue_per_set(
                ex.get('exercise_type', 'moderate_compound'),
                float(ex.get('rir', 2))
            )
            total_fatigue = fatigue * int(ex['sets'])

            execute_query("""
                INSERT INTO exercise_sets
                (id, session_id, user_id, exercise_name, exercise_type,
                 sets_performed, reps_performed, weight_lbs, rir, fatigue_per_set, total_fatigue)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), session_id, user_id,
                ex['name'], ex.get('exercise_type', 'moderate_compound'),
                ex['sets'], ex['reps'],
                float(ex.get('weight', 0)),
                float(ex.get('rir', 2)),
                fatigue, total_fatigue
            ))

        return jsonify({'success': True, 'session_id': session_id})

    return render_template('training/new_session.html', today=date.today())

@training_bp.route('/session/<session_id>')
@login_required
def view_session(session_id):
    user_id = session['user_id']

    session_data = execute_query("""
        SELECT id, session_date, session_type, notes
        FROM training_sessions
        WHERE id = %s AND user_id = %s
    """, (session_id, user_id), fetch='one')

    sets = execute_query("""
        SELECT exercise_name, exercise_type, sets_performed,
               reps_performed, weight_lbs, rir, fatigue_per_set, total_fatigue
        FROM exercise_sets
        WHERE session_id = %s
        ORDER BY created_at ASC
    """, (session_id,), fetch='all')

    return render_template('training/session_detail.html',
        session=session_data, sets=sets)

@training_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Given last performance, predict next session."""
    user_id = session['user_id']
    data = request.get_json()

    exercise_name = data.get('exercise_name')

    # Get last logged set for this exercise
    last_set = execute_query("""
        SELECT es.weight_lbs, es.reps_performed, es.rir
        FROM exercise_sets es
        JOIN training_sessions ts ON es.session_id = ts.id
        WHERE es.user_id = %s AND es.exercise_name = %s
        ORDER BY ts.session_date DESC, es.created_at DESC
        LIMIT 1
    """, (user_id, exercise_name), fetch='one')

    if not last_set:
        return jsonify({'error': 'No previous data for this exercise'}), 404

    prediction = predict_next_session(
        float(last_set['weight_lbs']),
        int(last_set['reps_performed']),
        float(last_set['rir'])
    )
    prediction['exercise'] = exercise_name
    return jsonify(prediction)

@training_bp.route('/checkin', methods=['POST'])
@login_required
def weekly_checkin():
    user_id = session['user_id']
    data = request.get_json()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)

    # Get user profile
    user = execute_query("""
        SELECT height_cm, birth_date, sex FROM users WHERE id = %s
    """, (user_id,), fetch='one')

    # Get last week's avg calories
    avg_calories = execute_query("""
        SELECT AVG(calories_in) as avg_cal
        FROM daily_logs
        WHERE user_id = %s AND date >= %s AND date < %s
    """, (user_id, last_week_start, week_start), fetch='one')

    # Get weight change last 2 weeks
    weight_data = execute_query("""
        SELECT date, weight_lbs FROM daily_logs
        WHERE user_id = %s AND date >= %s
        ORDER BY date ASC
    """, (user_id, last_week_start), fetch='all')

    # Calculate TDEE
    from app.model.progressive_overload import calculate_age
    age = calculate_age(user['birth_date'])
    
    # Get current weight
    current_weight = execute_query("""
        SELECT weight_lbs FROM daily_logs
        WHERE user_id = %s ORDER BY date DESC LIMIT 1
    """, (user_id,), fetch='one')
    
    weight = float(current_weight['weight_lbs']) if current_weight else 163.0

    bmr = mifflin_st_jeor(weight, float(user['height_cm']), age, user['sex'])

    # Use adaptive TDEE if enough data, otherwise Mifflin-St Jeor
    if weight_data and len(weight_data) >= 4 and avg_calories['avg_cal']:
        first_weight = float(weight_data[0]['weight_lbs'])
        last_weight = float(weight_data[-1]['weight_lbs'])
        days = (weight_data[-1]['date'] - weight_data[0]['date']).days or 1
        weekly_change = (last_weight - first_weight) / days * 7
        tdee = adaptive_tdee(float(avg_calories['avg_cal']), weekly_change)
    else:
        tdee = estimate_tdee(bmr, activity='moderate')

    # Auto-classify diet
    avg_cal = float(avg_calories['avg_cal']) if avg_calories['avg_cal'] else tdee
    diet_status = classify_diet(avg_cal, tdee)

    sleep_hours = float(data.get('sleep_hours', 7))
    stress = data.get('stress_level', 'moderate')

    f_cap = compute_f_cap(
        weight_lbs=weight,
        sleep_hours=sleep_hours,
        diet=diet_status,
        stress=stress,
        genetics='average'
    )

    execute_query("""
        INSERT INTO weekly_checkins
        (user_id, week_start, avg_sleep_hours, stress_level, diet_status, genetics, f_cap_computed)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, week_start) DO UPDATE SET
            avg_sleep_hours = EXCLUDED.avg_sleep_hours,
            stress_level = EXCLUDED.stress_level,
            diet_status = EXCLUDED.diet_status,
            f_cap_computed = EXCLUDED.f_cap_computed
    """, (user_id, week_start, sleep_hours, stress, diet_status, 'average', f_cap))

    return jsonify({
        'success': True,
        'f_cap': f_cap,
        'tdee': tdee,
        'diet_status': diet_status,
        'bmr': bmr
    })