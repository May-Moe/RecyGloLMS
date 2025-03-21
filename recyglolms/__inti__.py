import datetime
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager
from flask_apscheduler import APScheduler # Import APScheduler
import pymysql

# Install pymysql to replace MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/recyglolms'  # Connecting to phpmyadmin localhost database in development

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:pHAZKkSTgFnPyRGElSkBpihHMfGJkulG@switchback.proxy.rlwy.net:34745/railway'  # Connecting to railway database in production
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

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(announcement_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(assessment_bp)