from flask import render_template, request, redirect, flash, session, jsonify
from app.logs import logs_bp
from db.database import execute_query
from functools import wraps
from datetime import date

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated

@logs_bp.route('/daily', methods=['GET', 'POST'])
@login_required
def daily_log():
    if request.method == 'POST':
        user_id = session['user_id']
        log_date = request.form.get('date')
        weight = request.form.get('weight')

        # Auto-detect if user worked out based on training sessions
        session_today = execute_query("""
            SELECT id FROM training_sessions
            WHERE user_id = %s AND session_date = %s
        """, (user_id, log_date), fetch='one')

        workout_done = session_today is not None
        calories_burned = 300 if workout_done else 0

        existing = execute_query(
            "SELECT id FROM daily_logs WHERE user_id = %s AND date = %s",
            (user_id, log_date), fetch='one'
        )

        if existing:
            flash('You already logged this date.', 'error')
            return redirect('/logs/daily')

        execute_query("""
            INSERT INTO daily_logs 
            (user_id, date, weight_lbs, calories_burned, workout_done)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, log_date, weight, calories_burned, workout_done))

        flash('Log saved successfully!', 'success')
        return redirect('/dashboard')

    return render_template('logs/daily.html', today=date.today())

@logs_bp.route('/history')
@login_required
def history():
    user_id = session['user_id']
    logs = execute_query("""
        SELECT date, weight_lbs, calories_burned, workout_done
        FROM daily_logs
        WHERE user_id = %s
        ORDER BY date DESC
        LIMIT 30
    """, (user_id,), fetch='all')

    return render_template('logs/history.html', logs=logs)

@logs_bp.route('/edit/<log_date>', methods=['POST'])
@login_required
def edit_log(log_date):
    user_id = session['user_id']
    data = request.get_json()
    weight = data.get('weight')

    execute_query("""
        UPDATE daily_logs SET weight_lbs = %s
        WHERE user_id = %s AND date = %s
    """, (weight, user_id, log_date))

    return jsonify({'success': True})