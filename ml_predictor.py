# ml_predictor.py
# Machine Learning module for severity prediction

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import joblib
import os

class SeverityPredictor:
    def __init__(self, model_path: str = "severity_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.label_encoders = {}
        self.features = ['cause', 'location', 'vehicle_type', 'weather', 'lighting', 'road_characteristics', 'human_factors']

    def preprocess_data(self, df: pd.DataFrame) -> tuple:
        """Preprocess the accident data for training."""
        # Encode categorical variables
        X = df[self.features].copy()
        y = df['severity'].copy()

        for col in self.features:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            X[col] = self.label_encoders[col].fit_transform(X[col])

        severity_encoder = LabelEncoder()
        y_encoded = severity_encoder.fit_transform(y)

        return X, y_encoded, severity_encoder

    def train_model(self, csv_path: str = "accident_data.csv"):
        """Train the severity prediction model."""
        if not os.path.exists(csv_path):
            print(f"Data file {csv_path} not found. Cannot train model.")
            return None

        df = pd.read_csv(csv_path)

        # Need minimum data for training
        if len(df) < 10:
            print("Insufficient data for training. Need at least 10 samples.")
            return None

        X, y_encoded, severity_encoder = self.preprocess_data(df)

        X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)

        # Save model and encoders
        model_data = {
            'model': self.model,
            'label_encoders': self.label_encoders,
            'severity_encoder': severity_encoder,
            'features': self.features
        }
        joblib.dump(model_data, self.model_path)

        # Evaluate
        y_pred = self.model.predict(X_test)
        print("Model Training Results:")
        print(classification_report(y_test, y_pred, target_names=severity_encoder.classes_))

        return self.model

    def load_model(self):
        """Load the trained model."""
        if os.path.exists(self.model_path):
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.label_encoders = model_data['label_encoders']
            self.severity_encoder = model_data.get('severity_encoder')
            self.features = model_data.get('features', self.features)
            return True
        return False

    def predict_severity(self, accident_params: dict) -> tuple:
        """Predict accident severity and probability."""
        if self.model is None:
            if not self.load_model():
                return "unknown", 0.0

        # Prepare input data
        input_data = pd.DataFrame([accident_params])[self.features]

        # Encode
        for col in self.features:
            if col in self.label_encoders:
                try:
                    input_data[col] = self.label_encoders[col].transform(input_data[col])
                except ValueError:
                    # Unknown category, use most frequent
                    input_data[col] = self.label_encoders[col].transform([self.label_encoders[col].classes_[0]])

        # Predict
        prediction = self.model.predict(input_data)[0]
        probabilities = self.model.predict_proba(input_data)[0]

        severity = self.severity_encoder.inverse_transform([prediction])[0]
        confidence = probabilities[prediction]

        return severity.lower(), confidence

# Global predictor instance
predictor = SeverityPredictor()

def get_severity_prediction(cause: str, location: str, vehicle_type: str, weather: str, lighting: str, road_characteristics: str, human_factors: str) -> tuple:
    """Convenience function to get severity prediction."""
    params = {
        'cause': cause,
        'location': location,
        'vehicle_type': vehicle_type,
        'weather': weather,
        'lighting': lighting,
        'road_characteristics': road_characteristics,
        'human_factors': human_factors
    }
    return predictor.predict_severity(params)