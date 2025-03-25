import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager
from flask_apscheduler import APScheduler  # Import APScheduler
import pymysql
import logging
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Install pymysql to replace MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/recyglolms'  # Connecting to phpmyadmin localhost database in development
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pHAZKkSTgFnPyRGElSkBpihHMfGJkulG@switchback.proxy.rlwy.net:34745/railway'  # Connecting to railway database in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Set maximum file size to 100 MB

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)  # Initialize LoginManager
login_manager.login_view = 'auth.login'  # Set the default view for login

# Create a user loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from recyglolms.models import User  # Import User here to avoid circular import
    return User.query.get(int(user_id))  # Ensure User model is imported

# Import and register blueprints after extensions are initialized
from recyglolms.main import main_bp
from recyglolms.auth import auth_bp
from recyglolms.admin import admin_bp
from recyglolms.upload import upload_bp
from recyglolms.announcement import announcement_bp
from recyglolms.quiz import quiz_bp
from recyglolms.assesement import assessment_bp
from recyglolms.certificate_grading import grading_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(announcement_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(grading_bp)

# Initialize APScheduler
scheduler = APScheduler()

# Enable logging
logging.basicConfig(level=logging.DEBUG)
scheduler.add_listener(lambda event: logging.info(f"Event: {event}"), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

# Import models here to avoid circular import problem
from recyglolms.models import ActionLog, Notification

# Define the function to delete old logs
def delete_old_logs():
    """Deletes logs older than 3 days."""
    with app.app_context():
        three_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        print(f"Checking for logs older than {three_days_ago}")  # Log when the job runs
        old_logs = ActionLog.query.filter(ActionLog.timestamp < three_days_ago).all()

        print(f"Found {len(old_logs)} logs to delete.")  # Debugging
        if old_logs:
            for log in old_logs:
                db.session.delete(log)
            db.session.commit()
            print(f"Deleted {len(old_logs)} old logs.")

# Define the function to delete old notifications
def delete_old_notifications():
    """Deletes notifications older than 7 days."""
    with app.app_context():
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        print(f"Checking for notifications older than {seven_days_ago}")  # Log when the job runs
        old_notifications = Notification.query.filter(Notification.created_at < seven_days_ago).all()

        print(f"Found {len(old_notifications)} notifications to delete.")  # Debugging
        if old_notifications:
            for notification in old_notifications:
                db.session.delete(notification)
            db.session.commit()
            print(f"Deleted {len(old_notifications)} old notifications.")

# Initialize scheduler and add the delete_old_logs and delete_old_notifications jobs
if not scheduler.running:
    scheduler.init_app(app)
    scheduler.start()
    print("Scheduler started!")  # Log that scheduler started
    scheduler.add_job(id='delete_old_logs', func=delete_old_logs, trigger='interval', minutes=1)
    scheduler.add_job(id='delete_old_notifications', func=delete_old_notifications, trigger='interval', minutes=1)

# End of auto deleting features