import numpy as np
from datetime import date, timedelta

def predict_weight(logs):
    """
    Predict weight 14 days from now using weighted linear regression.
    Recent data points are weighted more heavily than older ones.
    """
    if len(logs) < 3:
        return None, None

    base_date = logs[0]['date']
    X = np.array([(log['date'] - base_date).days for log in logs], dtype=float)
    y = np.array([float(log['weight_lbs']) for log in logs])

    # Exponential weights — recent points matter more
    n = len(logs)
    weights = np.exp(np.linspace(0, 2, n))  # older=low weight, recent=high weight
    weights /= weights.sum()  # normalize

    # Weighted means
    X_mean = np.average(X, weights=weights)
    y_mean = np.average(y, weights=weights)

    # Weighted linear regression
    numerator = (weights * (X - X_mean) * (y - y_mean)).sum()
    denominator = (weights * (X - X_mean) ** 2).sum()

    if denominator == 0:
        return None, None

    slope = numerator / denominator
    intercept = y_mean - slope * X_mean

    # Predict 14 days from today
    today = date.today()
    days_from_base = (today - base_date).days + 14
    predicted = slope * days_from_base + intercept

    # R² confidence on unweighted residuals
    y_pred = slope * X + intercept
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    confidence = round(min(max(r2 * 100, 0), 100), 1)

    return round(float(predicted), 1), confidence