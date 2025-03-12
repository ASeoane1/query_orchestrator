from functools import wraps
from flask import Blueprint, jsonify, request

from app.jwt_manager import JWTManager

api = Blueprint('api', __name__)

jwt_manager = JWTManager(secret="secret_key")

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid"}), 403
        
        token = auth_header.split(" ")[1]
        try:
            payload = jwt_manager.read_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 403
        
        if payload.get('role') != 'admin':
            return jsonify({"error": "Admin role required"}), 403
        
        return f(*args, **kwargs)
    return decorated

@api.route('/')
def index():
    return "Runnig OK."

@api.route('/status')
def status():
    return {"status": "ok"}

@api.route('/generate-token', methods=['POST'])
@admin_required
def generate_token():
    """
    Endpoint to generate a JWT token.
    Expects a JSON payload with the following keys:
      - data: A dictionary with string keys and list of strings as values.
      - user: A string representing the username.
      - is_admin: A boolean indicating if the admin role should be added to the generated token.
    This endpoint requires that the requester has an admin role in the token provided in the Authorization header.
    """
    req_data = request.get_json()
    if not req_data:
        return jsonify({"error": "Missing JSON payload"}), 400

    # Validate required keys
    if 'user' not in req_data or 'data' not in req_data or 'is_admin' not in req_data:
        return jsonify({"error": "Missing one of the required keys: 'user', 'data', 'is_admin'"}), 400

    user = req_data['user']
    data = req_data['data']
    is_admin_param = req_data['is_admin']

    # Validate types
    if not isinstance(data, dict):
        return jsonify({"error": "'data' must be a dictionary"}), 400
    # Check that each value in data is a list of strings
    for key, value in data.items():
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            return jsonify({"error": f"Value for key '{key}' must be a list of strings"}), 400
    if not isinstance(user, str):
        return jsonify({"error": "'user' must be a string"}), 400
    if not isinstance(is_admin_param, bool):
        return jsonify({"error": "'is_admin' must be a boolean"}), 400

    # Generate the token using the provided data
    token = jwt_manager.create_token(data, user, is_admin_param)
    return jsonify({"token": token})

def register_routes(app):
    app.register_blueprint(api)
