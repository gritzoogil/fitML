-- User goals
CREATE TABLE IF NOT EXISTS user_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    goal_weight_lbs DECIMAL(6,2) NOT NULL,
    target_date DATE NOT NULL,
    daily_calorie_target INT NOT NULL,
    daily_protein_target DECIMAL(6,2) NOT NULL,
    daily_carb_target DECIMAL(6,2) NOT NULL,
    daily_fat_target DECIMAL(6,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exercises master list
CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    exercise_type VARCHAR NOT NULL,
    muscle_group VARCHAR NOT NULL,
    is_custom BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id)
);

-- Training sessions
CREATE TABLE IF NOT EXISTS training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_date DATE NOT NULL,
    session_type VARCHAR,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Exercise sets
CREATE TABLE IF NOT EXISTS exercise_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES training_sessions(id),
    user_id UUID REFERENCES users(id),
    exercise_name VARCHAR NOT NULL,
    exercise_type VARCHAR NOT NULL,
    sets_performed INT NOT NULL,
    reps_performed INT NOT NULL,
    weight_lbs DECIMAL(6,2) DEFAULT 0,
    rir DECIMAL(3,1) DEFAULT 2,
    fatigue_per_set DECIMAL(8,4),
    total_fatigue DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User model params
CREATE TABLE IF NOT EXISTS user_model_params (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE,
    f_base DECIMAL(8,4) DEFAULT 150.0,
    k1_base DECIMAL(8,4) DEFAULT 2.0,
    k2_base DECIMAL(8,4) DEFAULT 10.0,
    carry_over_rate DECIMAL(6,4) DEFAULT 0.3,
    data_points INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Food logs
CREATE TABLE IF NOT EXISTS food_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    meal_type VARCHAR,
    food_name VARCHAR NOT NULL,
    calories INT NOT NULL,
    protein_g DECIMAL(6,2) DEFAULT 0,
    carbs_g DECIMAL(6,2) DEFAULT 0,
    fat_g DECIMAL(6,2) DEFAULT 0,
    source VARCHAR DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Progress photos
CREATE TABLE IF NOT EXISTS progress_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    date DATE NOT NULL,
    photo_url VARCHAR,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);