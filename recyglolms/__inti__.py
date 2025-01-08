from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager  # Import LoginManager
import pymysql

# Install pymysql to replace MySQLdb
pymysql.install_as_MySQLdb()

# Initialize the Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/recyglolms'  # Update with your MySQL credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

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
from recyglolms.adduser import admin_bp
from recyglolms.upload import upload_bp
from recyglolms.announcement import announcement_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(announcement_bp)