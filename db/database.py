import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app

def get_db_connection():
    conn = psycopg2.connect(
        host=current_app.config['DB_HOST'],
        port=current_app.config['DB_PORT'],
        dbname=current_app.config['DB_NAME'],
        user=current_app.config['DB_USER'],
        password=current_app.config['DB_PASSWORD']
    )
    conn.autocommit = True
    return conn

def execute_query(query, params=None, fetch=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch == 'one':
                return cur.fetchone()
            elif fetch == 'all':
                return cur.fetchall()
    finally:
        conn.close()