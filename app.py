from flask import Flask, render_template, request, jsonify
import pickle
import requests
import numpy as np
from datetime import datetime
import random

app = Flask(__name__)

# Disable caching for development
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Load the pickle models
try:
    print("Loading models...")
    with open('rf_model.pkl', 'rb') as f:
        rf_model = pickle.load(f)
    print("RF model loaded")
    with open('xgb_model.pkl', 'rb') as f:
        xgb_model = pickle.load(f)
    print("XGB model loaded")
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("Scaler loaded")
    print("All models loaded successfully!")
except FileNotFoundError as e:
    print(f"Error loading models: {e}")
    raise
except MemoryError as e:
    print(f"Memory error while loading models: {e}")
    print("Try reducing model size or increasing available memory")
    raise
except Exception as e:
    print(f"Unexpected error loading models: {e}")
    raise

# AQI Categories and ranges
def get_aqi_category(aqi):
    if aqi <= 50:
        return {"category": "Good", "color": "#00e400"}
    elif aqi <= 100:
        return {"category": "Moderate", "color": "#ffff00"}
    elif aqi <= 150:
        return {"category": "Unhealthy for Sensitive Groups", "color": "#ff7e00"}
    elif aqi <= 200:
        return {"category": "Unhealthy", "color": "#ff0000"}
    elif aqi <= 300:
        return {"category": "Very Unhealthy", "color": "#8f3f97"}
    else:
        return {"category": "Hazardous", "color": "#7e0023"}

# Weather API endpoint and key
WEATHER_API_KEY = "ce79d530a5e242626b213e106d4ba37c"
WEATHER_API = "https://api.openweathermap.org/data/2.5/forecast"

# Air Quality API endpoint and key
API_KEY = "ce79d530a5e242626b213e106d4ba37c"
AQI_API = "https://api.openweathermap.org/data/2.5/air_pollution"
GEO_API = "https://api.openweathermap.org/geo/1.0/direct"

# Add TomTom API key
TOMTOM_API_KEY = "YOUR_TOMTOM_API_KEY"
TOMTOM_TRAFFIC_API = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

def calculate_traffic_timings(aqi_value, traffic_data):
    """Calculate traffic light timings based on AQI and traffic data for sustainable development"""
    # Dynamic base timings that scale with AQI - Less green time for low AQI, more green time for high AQI
    def get_base_timings(aqi):
        if aqi <= 50:  # Good
            return {'red': 90, 'yellow': 3, 'green': 30}  # Minimum green when air is clean
        elif aqi <= 100:  # Moderate
            return {'red': 75, 'yellow': 3, 'green': 45}
        elif aqi <= 150:  # Unhealthy for Sensitive Groups
            return {'red': 60, 'yellow': 3, 'green': 60}
        elif aqi <= 200:  # Unhealthy
            return {'red': 45, 'yellow': 3, 'green': 75}
        elif aqi <= 300:  # Very Unhealthy
            return {'red': 30, 'yellow': 3, 'green': 90}
        else:  # Hazardous
            return {'red': 20, 'yellow': 3, 'green': 120}  # Maximum green to reduce idle emissions

    base_timings = get_base_timings(aqi_value)
    
    # AQI-specific recommendations and strategies for sustainable development
    if aqi_value <= 50:
        recommendation = "Normal traffic regulation - Air quality can handle stops"
        strategy = "Longer red phases to regulate flow, air quality is excellent"
    elif aqi_value <= 100:
        recommendation = "Moderate flow adjustment - Balancing stops and movement"
        strategy = "Gradual increase in green phase as AQI rises"
    elif aqi_value <= 150:
        recommendation = "Equal phase distribution - Managing growing pollution"
        strategy = "Balanced red-green phases for moderate pollution levels"
    elif aqi_value <= 200:
        recommendation = "Enhanced flow priority - Reducing idle emissions"
        strategy = "Extended green phases to minimize vehicle stopping"
    elif aqi_value <= 300:
        recommendation = "Critical flow management - Minimizing idle time"
        strategy = "Long green phases to keep traffic moving"
    else:
        recommendation = "Emergency emission protocol - Maximum flow priority"
        strategy = "Minimal red phase to prevent pollution from idle vehicles"

    # Traffic congestion adjustments - Modified for sustainability
    congestion = traffic_data.get('congestion', 0)
    speed = traffic_data.get('speed', 0)
    
    # Traffic factor now considers both congestion and AQI
    # For high AQI, high congestion leads to longer green times
    # For low AQI, high congestion leads to balanced timing
    if aqi_value > 150:  # Poor air quality
        traffic_factor = 1.0 + (congestion / 100) * 0.3  # Increase green time with congestion
        final_timings = {
            'red': round(base_timings['red'] * (1 / traffic_factor)),
            'yellow': base_timings['yellow'],
            'green': round(base_timings['green'] * traffic_factor)
        }
    else:  # Good air quality
        traffic_factor = 1.0 + (congestion / 100) * 0.2  # Smaller adjustment for good air quality
        final_timings = {
            'red': round(base_timings['red'] * traffic_factor),
            'yellow': base_timings['yellow'],
            'green': round(base_timings['green'] * (1 / traffic_factor))
        }

    # Calculate emission reduction impact
    total_cycle = sum(final_timings.values())
    green_percentage = (final_timings['green'] / total_cycle) * 100
    emission_reduction = "High" if green_percentage > 60 else "Medium" if green_percentage > 40 else "Low"

    return {
        'timings': final_timings,
        'recommendation': f"{recommendation}\nStrategy: {strategy}",
        'traffic_data': {
            'density': f"{congestion}%",
            'speed': f"{speed} km/h",
            'queue': f"{round(congestion * 0.7)} vehicles",
            'cycle_length': f"{total_cycle} seconds",
            'emission_control': f"{emission_reduction} (Green phase: {green_percentage:.1f}%)"
        }
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        city = request.form['city']
        
        # Get city coordinates
        geo_params = {
            'q': city,
            'limit': 1,
            'appid': API_KEY
        }
        geo_response = requests.get(GEO_API, params=geo_params)
        geo_data = geo_response.json()
        
        if not geo_data:
            return jsonify({'error': f'City not found: {city}'})
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        
        # Get current weather data
        weather_params = {
            'lat': lat,
            'lon': lon,
            'appid': WEATHER_API_KEY,
            'units': 'metric'  # Use metric units
        }
        
        # Get current weather
        weather_response = requests.get('https://api.openweathermap.org/data/2.5/weather', params=weather_params)
        weather_data = weather_response.json()
        
        # Process weather data
        if weather_response.status_code == 200:
            weather = {
                'temp': round(weather_data['main']['temp']),
                'description': weather_data['weather'][0]['description'].capitalize(),
                'humidity': weather_data['main']['humidity'],
                'wind_speed': round(weather_data['wind']['speed'], 1),
                'uvi': 0  # Default UV index
            }
            
            # Get UV Index
            onecall_params = {
                'lat': lat,
                'lon': lon,
                'appid': WEATHER_API_KEY,
                'units': 'metric',
                'exclude': 'minutely,hourly,daily,alerts'
            }
            onecall_response = requests.get('https://api.openweathermap.org/data/3.0/onecall', params=onecall_params)
            if onecall_response.status_code == 200:
                onecall_data = onecall_response.json()
                weather['uvi'] = round(onecall_data['current']['uvi'], 1)
        else:
            weather = None
        
        # Get air quality data
        aqi_params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY
        }
        aqi_response = requests.get(AQI_API, params=aqi_params)
        aqi_data = aqi_response.json()
        
        if 'list' not in aqi_data or not aqi_data['list']:
            return jsonify({'error': 'No air quality data available for this location'})
        
        # Extract pollutant values
        components = aqi_data['list'][0]['components']
        
        # Create feature vector for ML models
        features = np.array([[
            components.get('pm2_5', 0),
            components.get('pm10', 0),
            components.get('so2', 0),
            components.get('nh3', 0),
            components.get('co', 0),
            components.get('no2', 0),
            components.get('o3', 0)
        ]])
        
        # Scale features
        scaled_features = scaler.transform(features)
        
        # Get predictions
        rf_aqi = rf_model.predict(scaled_features)[0]
        xgb_aqi = xgb_model.predict(scaled_features)[0]
        final_aqi = (rf_aqi + xgb_aqi) / 2
        
        # Get AQI category
        aqi_info = get_aqi_category(final_aqi)
        
        # Prepare response
        response = {
            'PM2.5': float(components.get('pm2_5', 0)),
            'PM10': float(components.get('pm10', 0)),
            'SO2': float(components.get('so2', 0)),
            'NO2': float(components.get('no2', 0)),
            'O3': float(components.get('o3', 0)),
            'CO': float(components.get('co', 0)),
            'NH3': float(components.get('nh3', 0)),
            'AQI': float(final_aqi),
            'AQI_category': aqi_info['category'],
            'AQI_color': aqi_info['color'],
            'latitude': float(lat),
            'longitude': float(lon),
            'weather': weather
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in predict route: {str(e)}")  # Log the error
        return jsonify({'error': str(e)})

@app.route('/traffic-data', methods=['POST'])
def get_traffic_data():
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        aqi = data.get('aqi')

        # Get traffic data from TomTom API
        params = {
            'key': TOMTOM_API_KEY,
            'point': f"{lat},{lon}",
            'unit': 'KMPH'
        }
        
        try:
            traffic_response = requests.get(TOMTOM_TRAFFIC_API, params=params)
            traffic_data = traffic_response.json()
            
            # Extract relevant traffic information
            current_speed = traffic_data.get('flowSegmentData', {}).get('currentSpeed', 0)
            free_flow_speed = traffic_data.get('flowSegmentData', {}).get('freeFlowSpeed', 1)
            
            # Calculate congestion percentage
            congestion = round((1 - (current_speed / free_flow_speed)) * 100) if free_flow_speed > 0 else 0
            congestion = max(0, min(100, congestion))  # Ensure between 0 and 100
            
            traffic_info = {
                'congestion': congestion,
                'speed': current_speed
            }
        except Exception as e:
            print(f"Error fetching traffic data: {e}")
            # Fallback to simulated data if API fails
            traffic_info = {
                'congestion': random.randint(30, 90),
                'speed': random.randint(20, 60)
            }

        # Calculate traffic light timings
        result = calculate_traffic_timings(aqi, traffic_info)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
