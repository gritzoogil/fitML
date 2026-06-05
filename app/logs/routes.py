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
        calories_in = request.form.get('calories_in')
        protein = request.form.get('protein')
        calories_burned = request.form.get('calories_burned')
        workout_done = request.form.get('workout_done') == 'on'

        existing = execute_query(
            "SELECT id FROM daily_logs WHERE user_id = %s AND date = %s",
            (user_id, log_date), fetch='one'
        )

        if existing:
            flash('You already logged this date. Use edit to update it.', 'error')
            return redirect('/logs/daily')

        execute_query("""
            INSERT INTO daily_logs 
            (user_id, date, weight_lbs, calories_in, protein_g, calories_burned, workout_done)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, log_date, weight, calories_in, protein, calories_burned, workout_done))

        flash('Log saved successfully!', 'success')
        return redirect('/logs/history')

    return render_template('logs/daily.html', today=date.today())

@logs_bp.route('/workout', methods=['GET', 'POST'])
@login_required
def workout_log():
    if request.method == 'POST':
        user_id = session['user_id']
        data = request.get_json()
        log_date = data.get('date')
        exercises = data.get('exercises', [])

        for exercise in exercises:
            execute_query("""
                INSERT INTO workout_logs
                (user_id, date, exercise, sets, reps, weight_lbs)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id, log_date,
                exercise['name'],
                exercise['sets'],
                exercise['reps'],
                exercise.get('weight', 0)
            ))

        return jsonify({'success': True})

    return render_template('logs/workout.html')

@logs_bp.route('/history')
@login_required
def history():
    user_id = session['user_id']
    logs = execute_query("""
        SELECT date, weight_lbs, calories_in, protein_g, 
               calories_burned, workout_done
        FROM daily_logs
        WHERE user_id = %s
        ORDER BY date DESC
        LIMIT 30
    """, (user_id,), fetch='all')

    return render_template('logs/history.html', logs=logs)