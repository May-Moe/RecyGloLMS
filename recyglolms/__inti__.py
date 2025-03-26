import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_mail import Mail  # Import Flask-Mail
import pymysql
import logging
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from config import MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER

# Install pymysql to replace MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/recyglolms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size

# Mail configuration
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)  # Initialize Flask-Mail
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from recyglolms.models import User
    return User.query.get(int(user_id))

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
    with app.app_context():
        three_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        old_logs = ActionLog.query.filter(ActionLog.timestamp < three_days_ago).all()
        if old_logs:
            for log in old_logs:
                db.session.delete(log)
            db.session.commit()

# Define the function to delete old notifications
def delete_old_notifications():
    with app.app_context():
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        old_notifications = Notification.query.filter(Notification.created_at < seven_days_ago).all()
        if old_notifications:
            for notification in old_notifications:
                db.session.delete(notification)
            db.session.commit()

# Initialize scheduler and add jobs
if not scheduler.running:
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id='delete_old_logs', func=delete_old_logs, trigger='interval', minutes=1)
    scheduler.add_job(id='delete_old_notifications', func=delete_old_notifications, trigger='interval', minutes=1)
