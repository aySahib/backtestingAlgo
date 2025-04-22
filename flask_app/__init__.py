import os
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Dev-friendly template reloading
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True
    # Load configuration from environment or defaults
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'DGX45RTQ7S536924815ZXB7T')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit

    # Import and register blueprints (controllers)
    from flask_app.controllers import mainController
    app.register_blueprint(mainController.bp)

    return app
