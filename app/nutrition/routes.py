from flask import render_template, request, jsonify, session, redirect
from app.nutrition import nutrition_bp
from db.database import execute_query
from functools import wraps
from datetime import date
import os
import json
import requests

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated

@nutrition_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    date_str = request.args.get('date', str(date.today()))
    
    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        selected_date = date.today()

    food_logs = execute_query("""
        SELECT id, meal_type, food_name, calories, protein_g, carbs_g, fat_g, source
        FROM food_logs
        WHERE user_id = %s AND date = %s
        ORDER BY created_at ASC
    """, (user_id, selected_date), fetch='all')

    totals = execute_query("""
        SELECT 
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(protein_g), 0) as total_protein,
            COALESCE(SUM(carbs_g), 0) as total_carbs,
            COALESCE(SUM(fat_g), 0) as total_fat
        FROM food_logs
        WHERE user_id = %s AND date = %s
    """, (user_id, selected_date), fetch='one')

    goals = execute_query("""
        SELECT daily_calorie_target, daily_protein_target, 
               daily_carb_target, daily_fat_target
        FROM user_goals WHERE user_id = %s
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,), fetch='one')

    return render_template('nutrition/index.html',
        food_logs=food_logs,
        totals=totals,
        goals=goals,
        today=date.today(),
        selected_date=selected_date
    )

@nutrition_bp.route('/add', methods=['POST'])
@login_required
def add_food():
    user_id = session['user_id']
    data = request.get_json()

    execute_query("""
        INSERT INTO food_logs
        (user_id, date, meal_type, food_name, calories, protein_g, carbs_g, fat_g, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        data.get('date', str(date.today())),
        data.get('meal_type', 'snack'),
        data['food_name'],
        data['calories'],
        data.get('protein_g', 0),
        data.get('carbs_g', 0),
        data.get('fat_g', 0),
        data.get('source', 'manual')
    ))

    return jsonify({'success': True})

@nutrition_bp.route('/estimate', methods=['POST'])
@login_required
def estimate_food():
    data = request.get_json()
    food_description = data.get('description', '')

    if not food_description:
        return jsonify({'error': 'No description provided'}), 400

    api_key = os.getenv("GROQ_API_KEY")

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a nutrition expert. Always respond with valid JSON only. No markdown, no backticks, no explanation."
                    },
                    {
                        "role": "user",
                        "content": f"""Estimate the calories and macros for this food: "{food_description}"

                Return ONLY a JSON object:
                {{
                    "food_name": "standardized name",
                    "calories": number,
                    "protein_g": number,
                    "carbs_g": number,
                    "fat_g": number,
                    "confidence": "high" or "medium" or "low",
                    "notes": "brief note about the estimate"
                }}"""
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            },
            timeout=30
        )

        result = response.json()
        text = result['choices'][0]['message']['content'].strip()
        text = text.replace('```json', '').replace('```', '').strip()
        nutrition_data = json.loads(text)
        nutrition_data['source'] = 'llm'
        return jsonify(nutrition_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@nutrition_bp.route('/delete/<log_id>', methods=['DELETE'])
@login_required
def delete_food(log_id):
    user_id = session['user_id']
    execute_query(
        "DELETE FROM food_logs WHERE id = %s AND user_id = %s",
        (log_id, user_id)
    )
    return jsonify({'success': True})

@nutrition_bp.route('/search')
@login_required
def search_food():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Split into words and search for any word match
    words = query.split()
    like_conditions = ' AND '.join([f"food_name ILIKE %s" for _ in words])
    params = [f'%{word}%' for word in words] + [query, f'{query}%']

    results = execute_query(f"""
        SELECT id, food_name, calories, protein_g, fat_g, carbs_g, fibre_g, sodium_mg
        FROM foods
        WHERE {like_conditions}
        ORDER BY 
            CASE WHEN LOWER(food_name) = LOWER(%s) THEN 0
                 WHEN LOWER(food_name) LIKE LOWER(%s) THEN 1
                 ELSE 2 END,
            LENGTH(food_name)
        LIMIT 10
    """, params, fetch='all')

    return jsonify([dict(r) for r in results])