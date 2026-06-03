import psycopg2
from datetime import date, timedelta

conn = psycopg2.connect(
    host='127.0.0.1', port='5432', dbname='fitml', user='postgres', password='')
cur = conn.cursor()

USER_ID = 'c6d22c04-6769-4993-969d-39924bbf27a9'

logs = [
    (date(2026, 5, 13), 167.5),
        (date(2026, 5, 14), 165.6),
    (date(2026, 5, 15), 165.0),
    (date(2026, 5, 17), 164.2),
    (date(2026, 5, 18), 164.6),
    (date(2026, 5, 20), 164.2),
    (date(2026, 5, 21), 163.4),
    (date(2026, 5, 22), 163.2),
    (date(2026, 5, 23), 162.6),
    (date(2026, 5, 24), 163.6),
    (date(2026, 5, 25), 163.6),
    (date(2026, 5, 27), 162.0),
    (date(2026, 5, 28), 163.6),
    (date(2026, 5, 31), 163.2),
    (date(2026, 6,  2), 162.2),
    (date(2026, 6,  3), 163.0),
]

for d, weight in logs:
    protein = round(weight * 0.7, 1)

    calories_in = 1750
    calories_burned = 300
    workout_done = True

    cur.execute("""
        INSERT INTO daily_logs
                (user_id, date, weight_lbs, calories_in, protein_g, calories_burned, workout_done)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (USER_ID, d, weight, calories_in, protein, calories_burned, workout_done))

conn.commit()
cur.close()
conn.close()
print(f"Seeded {len(logs)} daily logs for user {USER_ID}")