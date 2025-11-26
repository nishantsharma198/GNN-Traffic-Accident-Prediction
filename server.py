from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from app_logic import get_dynamic_route_prediction 
import os

# --- SERVER CONFIGURATION ---
app = Flask(__name__)
# Crucial for allowing the frontend to talk to the backend 
CORS(app) 
PORT = 5001 # Set a default port (using 5001 as 5000 was blocked)

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
    # Use send_file to serve the index.html from the current directory
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """
    Safely serves static files (like delhi_locations.js or favicon.ico).
    This uses send_from_directory, which fixes the FileNotFoundError you faced.
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
    
    # Note: If port 5001 is also blocked, try changing PORT = 5002, 5003, etc.
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)