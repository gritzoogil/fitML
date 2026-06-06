from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.logs import logs_bp
    from app.nutrition import nutrition_bp
    from app.training import training_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(training_bp)

    return app