from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager

def create_app(config_object: str | object = None):
    app = Flask(__name__, instance_relative_config=True)
    if config_object is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(config_object)

    # ensure instance folder exists (Flask's instance_path may not exist)
    import os
    os.makedirs(app.instance_path, exist_ok=True)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # register blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    from . import cli as cli_module

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)

    # register CLI commands
    cli_module.init_app(app)

    return app
