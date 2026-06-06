from datetime import date

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )

def mifflin_st_jeor(weight_lbs, height_cm, age, sex):
    """Calculate BMR using Mifflin-St Jeor equation."""
    weight_kg = weight_lbs * 0.453592
    if sex == 'male':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    return round(bmr, 2)

def estimate_tdee(bmr, activity='moderate'):
    """
    Activity multipliers:
    - sedentary: 1.2
    - light: 1.375
    - moderate (3-5x/week): 1.55
    - active (6-7x/week): 1.725
    """
    multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725
    }
    return round(bmr * multipliers.get(activity, 1.55), 0)

def adaptive_tdee(avg_daily_calories, avg_weekly_weight_change_lbs):
    """
    MacroFactor method — back-calculate TDEE from actual data.
    avg_weekly_weight_change_lbs: positive = gaining, negative = losing
    """
    return round(avg_daily_calories - (avg_weekly_weight_change_lbs * 3500 / 7), 0)

def classify_diet(actual_calories, tdee):
    """Classify diet status based on deficit/surplus."""
    diff = actual_calories - tdee
    if diff > 200:
        return 'surplus'
    elif diff > -200:
        return 'maintenance'
    elif diff > -500:
        return 'moderate_cut'
    else:
        return 'aggressive_cut'

def epley_1rm(weight, reps):
    return weight * (1 + reps / 30)

def brzycki_1rm(weight, reps):
    return weight / (1.0278 - 0.0278 * reps)

def lander_1rm(weight, reps):
    return (100 * weight) / (101.3 - 2.67123 * reps)

def average_1rm(weight, reps):
    if reps >= 15:
        return epley_1rm(weight, reps)
    e = epley_1rm(weight, reps)
    b = brzycki_1rm(weight, reps)
    l = lander_1rm(weight, reps)
    return round((e + b + l) / 3, 2)

def epley_reps(one_rm, new_weight):
    if new_weight >= one_rm:
        return 1
    return round((one_rm / new_weight - 1) * 30)

def brzycki_reps(one_rm, new_weight):
    if new_weight >= one_rm:
        return 1
    return round((1.0278 - new_weight / one_rm) / 0.0278)

def lander_reps(one_rm, new_weight):
    if new_weight >= one_rm:
        return 1
    return round((101.3 - (100 * new_weight / one_rm)) / 2.67123)

def predict_next_session(last_weight, last_reps, last_rir):
    if last_weight == 0:
        return {
            'next_weight': 0,
            'next_reps': last_reps + 1,
            'next_rir': last_rir,
            'one_rm': None,
            'progression': 'add_rep'
        }

    one_rm = average_1rm(last_weight, last_reps)
    next_weight = last_weight + 2.5
    predicted_reps_e = epley_reps(one_rm, next_weight)
    predicted_reps_b = brzycki_reps(one_rm, next_weight)
    predicted_reps_l = lander_reps(one_rm, next_weight)
    next_reps = round((predicted_reps_e + predicted_reps_b + predicted_reps_l) / 3)

    return {
        'next_weight': next_weight,
        'next_reps': next_reps,
        'next_rir': last_rir,
        'one_rm': round(one_rm, 1),
        'progression': 'increase_weight'
    }

def compute_fatigue_per_set(exercise_type, rir, training_age='intermediate', diet='moderate_cut', age_bracket='under_25'):
    k1 = 2.0
    k2 = 10.0

    m_ex = {
        'isolation': 0.5,
        'moderate_compound': 1.0,
        'heavy_axial': 1.8
    }.get(exercise_type, 1.0)

    m_exp = {
        'beginner': 0.6,
        'intermediate': 1.0,
        'advanced': 1.5
    }.get(training_age, 1.0)

    m_diet = {
        'surplus': 1.0,
        'maintenance': 1.1,
        'moderate_cut': 1.3,
        'aggressive_cut': 1.6
    }.get(diet, 1.3)

    m_age = {
        'under_25': 0.9,
        '25_to_35': 1.0,
        '36_to_45': 1.2,
        '46_plus': 1.4
    }.get(age_bracket, 0.9)

    structural = k1 * m_ex
    neurological = (k2 * m_exp) / (rir + 1)

    return round(m_diet * m_age * (structural + neurological), 4)

def compute_f_cap(weight_lbs, sleep_hours=7, diet='moderate_cut', stress='moderate', genetics='average'):
    f_base = 150.0

    r_diet = {
        'surplus': 1.2,
        'maintenance': 1.0,
        'moderate_cut': 0.8,
        'aggressive_cut': 0.6
    }.get(diet, 0.8)

    r_sleep = 1.2 if sleep_hours >= 8 else 1.0 if sleep_hours >= 7 else 0.7 if sleep_hours >= 6 else 0.4

    r_stress = {
        'low': 1.1,
        'moderate': 1.0,
        'high': 0.7,
        'severe': 0.4
    }.get(stress, 1.0)

    r_gen = {
        'high': 1.2,
        'average': 1.0,
        'poor': 0.8
    }.get(genetics, 1.0)

    return round(f_base * r_diet * r_sleep * r_stress * r_gen, 2)