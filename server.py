from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from app_logic import get_dynamic_route_prediction # Import core logic
import os

# --- SERVER CONFIGURATION ---
# IMPORTANT: The Flask instance must be named 'app' for Gunicorn to find it easily.
app = Flask(__name__)
# Enable CORS for cross-origin requests
CORS(app) 
PORT = 5001 # Retain 5001 for local testing, but Render ignores this port number.

# --- API ENDPOINT ---
@app.route('/predict_risk', methods=['POST'])
def predict_risk():
    """Receives coordinates and runs the GNN shortest path calculation."""
    data = request.get_json()
    
    try:
        # Coordinates come in as string "lat,lon" from the web app
        orig_lat, orig_lon = map(float, data['start_coords'].split(','))
        dest_lat, dest_lon = map(float, data['end_coords'].split(','))
    except (KeyError, ValueError):
        return jsonify({"status": "Invalid Input", "error": "Missing or malformed coordinates."}), 400

    print(f"Processing: {orig_lat},{orig_lon} to {dest_lat},{dest_lon}")
    
    # Run the robust graph-based prediction logic from app_logic.py
    result = get_dynamic_route_prediction(orig_lat, orig_lon, dest_lat, dest_lon)
    
    return jsonify(result)

# --- SERVING STATIC FILES ---

@app.route('/')
def serve_index():
    """Serves the main HTML dashboard file (index.html)."""
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """
    Safely serves static files (like delhi_locations.js).
    """
    try:
        # Serve the file from the current working directory (represented by '.')
        return send_from_directory('.', filename)
    except FileNotFoundError:
        # Gracefully handle requests for non-existent files (like favicon.ico)
        return "File Not Found", 404 


if __name__ == '__main__':
    print("\n--- GNN Prediction Server Started ---")
    print("WARNING: First request will be slow (10-20s) due to graph loading.")
    print(f"Access the web app at: http://127.0.0.1:{PORT}/")
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)