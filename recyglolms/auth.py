from flask import Blueprint, render_template, request, redirect, url_for, flash
from recyglolms.__inti__ import db, bcrypt
from recyglolms.models import User
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

# Create Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

# Create root admin before app request
@auth_bp.before_app_request
def create_root_admin():
    # Root admin credentials
    root_email = 'admin@recyglo.com'
    root_password = 'admin1234'
    

    # Check if the admin already exists
    admin = User.query.filter_by(email=root_email).first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash(root_password).decode('utf-8')
        root_admin = User(email=root_email, password=hashed_password, role=1)  # Assign role as 'admin'
        db.session.add(root_admin)
        db.session.commit()
        print("Root admin account created with email:", root_email)

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve email and password from form
        email = request.form['email']
        password = request.form['password']

        # Query the database for a user with the entered email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password, password):
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log in the user
            login_user(user)
            flash('Login successful!', 'success')

            # Redirect based on role
            if user.role == 1:
                return redirect(url_for('admin.dashboard'))  # Admin dashboard
            elif user.role == 0:
                return redirect(url_for('main.home'))  # User dashboard
        else:
            # Invalid email or password
            flash('Invalid email or password.', 'danger')

    # Render the login template
    return render_template('login.html')

# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    # Log out the user
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))