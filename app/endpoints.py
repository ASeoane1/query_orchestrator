from functools import wraps
from flask import Blueprint, jsonify, request

from app.jwt_manager import JWTManager

class API:
    def __init__(self, jwt_manager):
        """
        Inicializa la API con el JWT manager recibido.

        :param jwt_manager: Instancia de JWTManager para crear y leer tokens.
        """
        self.jwt_manager = jwt_manager
        self.blueprint = Blueprint('api', __name__)
        self.register_routes()

    def admin_required(self,f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Authorization header missing or invalid"}), 403
            
            token = auth_header.split(" ")[1]
            try:
                payload = self.jwt_manager.read_token(token)
            except Exception:
                return jsonify({"error": "Invalid token"}), 403
            
            if payload.get('role') != 'admin':
                return jsonify({"error": "Admin role required"}), 403
            
            return f(*args, **kwargs)
        return decorated

    def register_routes(self):
        """
        Registra los endpoints de la API en el blueprint.
        """

        @self.blueprint.route('/')
        def index():
            return "Running OK."

        @self.blueprint.route('/status')
        def status():
            return {"status": "ok"}

        @self.blueprint.route('/generate-token', methods=['POST'])
        @self.admin_required
        def generate_token():
            """
            Endpoint para generar un token JWT.
            Recibe un JSON con las claves:
              - data: Diccionario con claves string y valores listas de strings.
              - user: Nombre de usuario.
              - is_admin: Booleano que indica si se añade el rol de admin al token.
            Este endpoint requiere que la petición incluya en el header un token con rol de admin.
            """
            req_data = request.get_json()
            if not req_data:
                return jsonify({"error": "Missing JSON payload"}), 400

            # Validar que se incluyan las claves requeridas
            if 'user' not in req_data or 'data' not in req_data or 'is_admin' not in req_data:
                return jsonify({"error": "Missing one of the required keys: 'user', 'data', 'is_admin'"}), 400

            user = req_data['user']
            data = req_data['data']
            is_admin_param = req_data['is_admin']

            # Validar tipos de datos
            if not isinstance(data, dict):
                return jsonify({"error": "'data' must be a dictionary"}), 400

            # Verificar que cada valor de data sea una lista de strings
            for key, value in data.items():
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    return jsonify({"error": f"Value for key '{key}' must be a list of strings"}), 400

            if not isinstance(user, str):
                return jsonify({"error": "'user' must be a string"}), 400

            if not isinstance(is_admin_param, bool):
                return jsonify({"error": "'is_admin' must be a boolean"}), 400

            # Generar el token usando el jwt_manager recibido
            token = self.jwt_manager.create_token(data, user, is_admin_param)
            return jsonify({"token": token})

    def register(self, app):
        """
        Registra el blueprint de la API en la aplicación Flask.
        
        :param app: Instancia de Flask.
        """
        app.register_blueprint(self.blueprint)
