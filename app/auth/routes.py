import os
from flask import render_template, request, redirect, session, jsonify
from app.auth import auth_bp
from db.database import execute_query
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

if not firebase_admin._apps:
    cred = credentials.Certificate('config/firebase_credentials.json')
    firebase_admin.initialize_app(cred)

@auth_bp.route('/login')
def login():
    return render_template('auth/login.html', firebase_config={
        'apiKey': os.getenv('FIREBASE_API_KEY'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID'),
    })


@auth_bp.route('/register')
def register():
    return render_template('auth/register.html', firebase_config={
        'apiKey': os.getenv('FIREBASE_API_KEY'),
        'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
        'appId': os.getenv('FIREBASE_APP_ID'),
    })

@auth_bp.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        decoded = firebase_auth.verify_id_token(id_token)
        uid = decoded['uid']
        email = decoded['email']

        user = execute_query(
            "SELECT * FROM users WHERE firebase_uid = %s",
            (uid,), fetch='one'
        )

        if not user:
            execute_query(
                "INSERT INTO users (id, firebase_uid, email) VALUES (gen_random_uuid(), %s, %s)",
                (uid, email)
            )
            user = execute_query(
                "SELECT * FROM users WHERE firebase_uid = %s",
                (uid,), fetch='one'
            )

        session['user_id'] = str(user['id'])
        session['email'] = email
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 401

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/auth/login')