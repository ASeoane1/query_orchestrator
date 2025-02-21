import os
import yaml
from flask import Flask
from .startup import startup

def load_config():
    """Load config yaml"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)

    return config

def init_app():
    """Run Flask"""
    app = Flask(__name__)

    # Load config
    config = load_config()
    app.config.update(config)

    #Autopopulate native database
    startup(config)

    # Load endpoints
    from .endpoints import register_routes
    register_routes(app)

    return app
