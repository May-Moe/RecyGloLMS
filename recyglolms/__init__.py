from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import os
import logging
import pymysql
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from config import STORAGE_BUCKET

# Install pymysql to replace MySQLdb
pymysql.install_as_MySQLdb()

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
scheduler = APScheduler()
migrate = Migrate() # Create a Migrate instance

def create_app():
    app = Flask(__name__)
    #  Load config from environment or config.py
    app.config.from_object('config')

    # App Config
    try:
        from config import SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    except ImportError as e:
        raise RuntimeError("Database configuration is missing. Ensure 'config.py' is properly set up.") from e

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoids warnings
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'xz'}
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size

    #  Add Google Cloud Storage bucket config
    app.config["STORAGE_BUCKET"] = STORAGE_BUCKET  

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db) # Initialize Migrate with the app and db
    login_manager.login_view = 'auth.login'
    scheduler.init_app(app)

    # Enable logging
    logging.basicConfig(level=logging.DEBUG)
    scheduler.add_listener(lambda event: logging.info(f"Event: {event}"), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # IMPORTANT: Remove db.create_all(). Migrations will handle the database schema.
    # with app.app_context():
    #     from recyglolms import models
    #     db.create_all()

    # Register blueprints after initializing the database
    from recyglolms.main import main_bp
    from recyglolms.auth import auth_bp
    from recyglolms.admin import admin_bp
    from recyglolms.upload import upload_bp
    from recyglolms.announcement import announcement_bp
    from recyglolms.quiz import quiz_bp
    from recyglolms.assesement import assessment_bp
    from recyglolms.certificate_grading import grading_bp
    from recyglolms.events import events_bp # Import your new events blueprint

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(events_bp) # Register the events blueprint

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from recyglolms.models import User
        return User.query.get(int(user_id))

    return app