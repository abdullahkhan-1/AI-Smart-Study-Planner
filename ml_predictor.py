# =============================================================================
# ml_predictor.py — Machine Learning Study Time Predictor
# Smart Study Planner | SE Spring 2026
# =============================================================================
# MODEL: Linear Regression (scikit-learn)
#
# WHAT IT LEARNS:
#   Given a task's difficulty, importance, and your initial hour estimate,
#   predict how many hours you will ACTUALLY need based on past performance.
#
# TRAINING DATA (built from your own history):
#   X (features) = [difficulty, importance, planned_hours]
#   y (target)   = actual_hours logged in Progress tracker
#
# COLD START:
#   If fewer than 3 past data points exist, a heuristic fallback is used.
#   Once you have 3+ completed tasks, the real ML model takes over.
# =============================================================================

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np


# =============================================================================
# Heuristic fallback (used when not enough training data)
# =============================================================================

def heuristic_estimate(difficulty: int, importance: int,
                        planned_hours: float) -> float:
    """
    Rule-based formula used before ML model has enough data.

    Logic:
      - Hard subjects (difficulty 4-5) tend to need 20-40% more time
      - Important subjects get a small bump too
      - Returns adjusted estimate
    """
    difficulty_multiplier = 1.0 + (difficulty - 3) * 0.12   # ±12% per level from 3
    importance_multiplier = 1.0 + (importance  - 3) * 0.05   # ±5%  per level from 3
    adjusted = planned_hours * difficulty_multiplier * importance_multiplier
    return round(max(1.0, adjusted), 1)


# =============================================================================
# ML Predictor Class
# =============================================================================

class StudyTimePredictor:
    """
    Wraps a scikit-learn Linear Regression model.

    Features used:
      [0] difficulty    (1–5)
      [1] importance    (1–5)
      [2] planned_hours (user's initial estimate)

    Target:
      actual_hours (total hours user actually logged for that subject)
    """

    MIN_SAMPLES = 3   # Minimum data points before ML model is used

    def __init__(self):
        self.model   = LinearRegression()
        self.scaler  = StandardScaler()   # Normalises features for better fit
        self.trained = False
        self.n_samples = 0

    def _build_training_data(self, tasks: list, completed: list):
        """
        Joins tasks with progress to build (X, y) training pairs.

        For each subject that has BOTH a task entry AND logged progress hours,
        we create one training sample.
        """
        # Sum actual hours logged per subject
        actual_hours = {}
        for session in completed:
            subj = session["subject"]
            actual_hours[subj] = actual_hours.get(subj, 0) + session["hours_done"]

        X, y = [], []
        for task in tasks:
            subj = task["subject"]
            if subj in actual_hours and actual_hours[subj] > 0:
                X.append([
                    task["difficulty"],
                    task["importance"],
                    task["study_hours"],   # planned hours
                ])
                y.append(actual_hours[subj])   # actual hours

        return np.array(X) if X else None, np.array(y) if y else None

    def train(self, tasks: list, completed: list) -> dict:
        """
        Train (or re-train) the model on current data.
        Returns a status dict for display in the UI.
        """
        X, y = self._build_training_data(tasks, completed)

        if X is None or len(X) < self.MIN_SAMPLES:
            self.trained   = False
            self.n_samples = len(X) if X is not None else 0
            return {
                "trained"   : False,
                "n_samples" : self.n_samples,
                "message"   : f"Need {self.MIN_SAMPLES - self.n_samples} more completed "
                              f"task(s) to train the ML model. Using heuristic formula for now.",
                "mode"      : "heuristic"
            }

        # Scale features (important for Linear Regression stability)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        self.trained   = True
        self.n_samples = len(X)

        # Calculate R² score (how well model fits the data)
        r2 = self.model.score(X_scaled, y)

        # Extract coefficients for explanation
        coef = self.model.coef_
        return {
            "trained"    : True,
            "n_samples"  : self.n_samples,
            "r2_score"   : round(r2, 3),
            "message"    : f"Model trained on {self.n_samples} data point(s). "
                           f"R² score: {round(r2, 3)} "
                           f"({'good fit' if r2 > 0.7 else 'improving with more data'})",
            "mode"       : "ml",
            "coefficients": {
                "difficulty"    : round(float(coef[0]), 3),
                "importance"    : round(float(coef[1]), 3),
                "planned_hours" : round(float(coef[2]), 3),
            }
        }

    def predict(self, difficulty: int, importance: int,
                planned_hours: float) -> dict:
        """
        Predict actual hours needed for a new task.
        Returns prediction + which mode was used.
        """
        if not self.trained:
            predicted = heuristic_estimate(difficulty, importance, planned_hours)
            return {
                "predicted_hours" : predicted,
                "mode"            : "heuristic",
                "difference"      : round(predicted - planned_hours, 1),
                "message"         : "Heuristic estimate (not enough data for ML yet)"
            }

        X_new     = np.array([[difficulty, importance, planned_hours]])
        X_scaled  = self.scaler.transform(X_new)
        predicted = float(self.model.predict(X_scaled)[0])
        predicted = round(max(1.0, predicted), 1)   # Never predict less than 1h

        diff = round(predicted - planned_hours, 1)
        if diff > 0:
            msg = f"ML model suggests you may need {diff}h more than estimated."
        elif diff < 0:
            msg = f"ML model suggests your estimate may be {abs(diff)}h too high."
        else:
            msg = "ML model agrees with your estimate."

        return {
            "predicted_hours" : predicted,
            "mode"            : "ml",
            "difference"      : diff,
            "message"         : msg
        }


# =============================================================================
# Singleton instance — one predictor shared across the app
# =============================================================================

_predictor_instance = None

def get_predictor() -> StudyTimePredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = StudyTimePredictor()
    return _predictor_instance