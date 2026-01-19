import pandas as pd
import joblib

model = joblib.load("ML_model/ML_model.pkl")

def predict_condition(numeric_data):
    features = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
    X = pd.DataFrame([[numeric_data[f] for f in features]], columns=features)
    prediction = model.predict(X)[0]
    return "Abnormal" if prediction == 1 else "Normal"
