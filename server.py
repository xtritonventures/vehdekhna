from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from functools import wraps
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)
CORS(app)
app.secret_key = "bus-tracking-secret"

# ------------------------
# In-memory storage
# ------------------------
bus_locations = {}

# ------------------------
# Admin credentials
# ------------------------
ADMIN_USERS = {
    "adminA": "A",
    "adminB": "B",
    "adminC": "C",
    "adminD": "D",
    "adminE": "E",
    "adminF": "F"
}
ADMIN_PASSWORD = "boldswiftsure"

# ------------------------
# Auth decorator
# ------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

# ------------------------
# Login API
# ------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in ADMIN_USERS and password == ADMIN_PASSWORD:
        session['user'] = username
        session['group'] = ADMIN_USERS[username]
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "unauthorized"}), 401

# ------------------------
# Temp Debug Route
# ------------------------
@app.route('/debug-tile/<int:z>/<int:x>/<int:y>')
def debug_tile(z, x, y):
    import os

    base = os.path.dirname(os.path.abspath(__file__))
    tile_path = os.path.join(
        base, 'static', 'tiles', str(z), str(x), f'{y}.png'
    )

    return {
        "requested": f"{z}/{x}/{y}.png",
        "absolute_path": tile_path,
        "exists": os.path.exists(tile_path),
        "is_file": os.path.isfile(tile_path),
        "parent_exists": os.path.exists(os.path.dirname(tile_path)),
        "parent_contents": (
            os.listdir(os.path.dirname(tile_path))
            if os.path.exists(os.path.dirname(tile_path))
            else []
        )
    }


# ------------------------
# Driver location update
# ------------------------
@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.get_json()

    bus_id = data.get("busId")
    group = data.get("group")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if bus_id and group and latitude and longitude:
        bus_locations[bus_id] = {
            "group": group.upper(),
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": int(time.time())
        }
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 400

# ------------------------
# Dashboard data (group filtered)
# ------------------------
@app.route('/locations/', methods=['GET'])
@login_required
def get_locations():
    now = int(time.time())
    selected_group = request.args.get("group")

    result = {}
    for bus_id, info in bus_locations.items():
        if now - info["timestamp"] > 60:
            continue
        if selected_group and info["group"] != selected_group:
            continue
        result[bus_id] = info

    return jsonify(result)

# ------------------------
# Static pages
# ------------------------
@app.route('/driver/')
def serve_driver():
    return send_from_directory('driver', 'index.html')

@app.route('/dashboard/')
def serve_dashboard():
    return send_from_directory('dashboard', 'login.html')

@app.route('/dashboard/view')
def serve_dashboard_view():
    return send_from_directory('dashboard', 'dashboard.html')

# ------------------------
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

