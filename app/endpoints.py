from flask import Blueprint

api = Blueprint('api', __name__)

@api.route('/')
def index():
    return "Runnig OK."

@api.route('/status')
def status():
    return {"status": "ok"}

def register_routes(app):
    app.register_blueprint(api)
