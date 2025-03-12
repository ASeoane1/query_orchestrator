import os
import yaml
from flask import Flask

from app.endpoints import API
from app.jwt_manager import JWTManager
from .startup import Startup

def load_config(config_path=None):
    """
    Load yaml configuration file.
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml'
        )
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    
    return config

def init_app(config_path=None):
    """IRun flask."""
    app = Flask(__name__)

    config = load_config(config_path)
    app.config.update(config)

    startup = Startup(config)
    startup.run()

    jwt_manager = JWTManager(secret=config.get("secret"))
    api_instance = API(jwt_manager)
    api_instance.register(app)

    return app