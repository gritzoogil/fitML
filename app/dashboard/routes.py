from flask import render_template, session, redirect
from app.dashboard import dashboard_bp
from db.database import execute_query
from app.model.weight_predictor import predict_weight
from app.model.progressive_overload import compute_f_cap
from functools import wraps
from datetime import date, timedelta

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated

@dashboard_bp.route('/')
@dashboard_bp.route('')
@login_required
def index():
    user_id = session['user_id']
    today = date.today()

    # Weight logs for chart + prediction
    weight_logs = execute_query("""
        SELECT date, weight_lbs FROM daily_logs
        WHERE user_id = %s AND weight_lbs IS NOT NULL
        ORDER BY date ASC
    """, (user_id,), fetch='all')

    # ML prediction
    predicted_weight, confidence = predict_weight(weight_logs) if weight_logs else (None, None)

    # Today's macros
    today_macros = execute_query("""
        SELECT 
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(protein_g), 0) as total_protein,
            COALESCE(SUM(carbs_g), 0) as total_carbs,
            COALESCE(SUM(fat_g), 0) as total_fat
        FROM food_logs
        WHERE user_id = %s AND date = %s
    """, (user_id, today), fetch='one')

    # Today's daily log
    today_log = execute_query("""
        SELECT weight_lbs, workout_done
        FROM daily_logs
        WHERE user_id = %s AND date = %s
    """, (user_id, today), fetch='one')

    # Goals
    goals = execute_query("""
        SELECT * FROM user_goals
        WHERE user_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,), fetch='one')

    # Fatigue this week
    week_start = today - timedelta(days=today.weekday())
    checkin = execute_query("""
        SELECT * FROM weekly_checkins
        WHERE user_id = %s AND week_start = %s
    """, (user_id, week_start), fetch='one')

    weekly_fatigue = execute_query("""
        SELECT COALESCE(SUM(total_fatigue), 0) as total
        FROM exercise_sets
        WHERE user_id = %s AND created_at >= %s
    """, (user_id, week_start), fetch='one')

    f_cap = None
    f_total = float(weekly_fatigue['total']) if weekly_fatigue else 0
    net_balance = None

    if checkin:
        f_cap = compute_f_cap(
            weight_lbs=float(weight_logs[-1]['weight_lbs']) if weight_logs else 163.0,
            sleep_hours=float(checkin['avg_sleep_hours']),
            diet=checkin['diet_status'],
            stress=checkin['stress_level'],
            genetics=checkin['genetics']
        )
        net_balance = round(f_cap - f_total, 2)

    # Chart data
    chart_labels = [str(log['date']) for log in weight_logs]
    chart_weights = [float(log['weight_lbs']) for log in weight_logs]

    # Add prediction point
    if predicted_weight:
        future_date = today + timedelta(days=14)
        chart_labels.append(str(future_date))
        chart_weights.append(None)  # gap in actual data
        predicted_point = predicted_weight
    else:
        predicted_point = None

    # Current weight
    current_weight = float(weight_logs[-1]['weight_lbs']) if weight_logs else None

    # Days to goal
    days_to_goal = (goals['target_date'] - today).days if goals else None

    return render_template('dashboard/index.html',
        today=today,
        current_weight=current_weight,
        predicted_weight=predicted_weight,
        confidence=confidence,
        predicted_point=predicted_point,
        chart_labels=chart_labels,
        chart_weights=chart_weights,
        today_macros=today_macros,
        today_log=today_log,
        goals=goals,
        f_cap=f_cap,
        f_total=round(f_total, 2),
        net_balance=net_balance,
        days_to_goal=days_to_goal
    )