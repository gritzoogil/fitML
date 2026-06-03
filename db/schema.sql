-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  firebase_uid VARCHAR UNIQUE NOT NULL,
  email VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily logs table
CREATE TABLE daily_logs (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  weight_lbs DECIMAL,
  calories_in INT,
  protein_g DECIMAL,
  calories_burned INT,
  workout_done BOOLEAN,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Workout logs table
CREATE TABLE workout_logs (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  date DATE NOT NULL,
  exercise VARCHAR,
  sets INT,
  reps INT,
  weight_lbs DECIMAL
);

-- Predictions table
CREATE TABLE predictions (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  predicted_at TIMESTAMP DEFAULT NOW(),
  target_date DATE,
  predicted_weight DECIMAL,
  confidence_score DECIMAL
);