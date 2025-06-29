from flask import Flask, render_template, request
import pickle
import numpy as np

app = Flask(__name__)

# Load the trained models and scaler
with open("rf_model.pkl", "rb") as file:
    rf_model = pickle.load(file)

with open("xgb_model.pkl", "rb") as file:
    xgb_model = pickle.load(file)

with open("scaler.pkl", "rb") as file:
    scaler = pickle.load(file)

# Hardcoded city data
city_data = {
    "Delhi": [200, 30, 40, 50, 25, 1.2, 15, 60],
    "Mumbai": [100, 20, 25, 30, 18, 0.8, 10, 50],
    "Kolkata": [150, 25, 35, 40, 22, 1.0, 12, 55],
    "Bangalore": [80, 10, 15, 20, 12, 0.5, 8, 45],
    "Chennai": [90, 12, 18, 22, 14, 0.6, 9, 48]
}

# Function to classify AQI levels based on PM2.5 value
def classify_air_quality(pm25):
    if pm25 <= 50:
        return "Good ✅"
    elif pm25 <= 100:
        return "Moderate 🟡"
    elif pm25 <= 150:
        return "Unhealthy for Sensitive Groups 🟠"
    elif pm25 <= 200:
        return "Unhealthy 🔴"
    elif pm25 <= 300:
        return "Very Unhealthy 🟣"
    else:
        return "Hazardous ☠️"

@app.route("/", methods=["GET", "POST"])
def index():
    prediction_rf, prediction_xgb = None, None
    quality_rf, quality_xgb = None, None
    selected_city = None

    if request.method == "POST":
        selected_city = request.form["city"]
        features = np.array([city_data[selected_city]]).reshape(1, -1)

        # Scale the input data
        features_scaled = scaler.transform(features)

        # Predict using both models
        prediction_rf = rf_model.predict(features_scaled)[0]
        prediction_xgb = xgb_model.predict(features_scaled)[0]

        # Classify air quality based on predicted PM2.5 values
        quality_rf = classify_air_quality(prediction_rf)
        quality_xgb = classify_air_quality(prediction_xgb)

    return render_template("index.html", cities=city_data.keys(),
                           selected_city=selected_city,
                           prediction_rf=prediction_rf,
                           prediction_xgb=prediction_xgb,
                           quality_rf=quality_rf,
                           quality_xgb=quality_xgb)

if __name__ == "__main__":
    app.run(debug=True)
