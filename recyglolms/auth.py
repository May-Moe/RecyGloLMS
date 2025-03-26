from mailbox import Message
import random
import string
from flask import Blueprint, render_template, request, redirect, url_for, flash
from recyglolms.__inti__ import db, bcrypt, mail
from recyglolms.models import PasswordReset, User
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
import pytz

from datetime import datetime, timedelta

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

            # Redirect admins and sub-admins to the same dashboard
            if user.role in [1, 2]:  
                return redirect(url_for('admin.dashboard'))  # Admin & Sub-Admin Dashboard
            elif user.role == 0:
                return redirect(url_for('main.home'))  # User Dashboard
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

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if the email exists in the system
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate a one-time password (OTP)
            otp = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Save the OTP to the PasswordReset model
            password_reset = PasswordReset(user_id=user.userid, otp=otp, created_at=datetime.utcnow())  
            db.session.add(password_reset)
            db.session.commit()

            # Temporarily bypass email sending
            # msg = Message(
            #     subject="Password Reset OTP",
            #     recipients=[email],
            #     body=f"Your OTP for password reset is: {otp}"
            # )
            # mail.send(msg)  # This line is commented out to avoid the email sending error
            
            # Redirect directly to the OTP verification page
            flash('OTP generated. Please proceed to verify your OTP.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Email address not found. Please check and try again.', 'danger')
    
    return render_template('forgot_password.html')



from datetime import datetime
import pytz

@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form.get('otp')  # Use .get() to prevent KeyError
        new_password = request.form.get('new_password')  # Use .get() to avoid KeyError
        
        if not otp or not new_password:
            flash('OTP and New Password are required.', 'danger')
            return render_template('otp_login.html')

        # Debugging: Print the received form data
        print("Received form data:", request.form)

        # Fetch the password reset record
        password_reset = PasswordReset.query.filter_by(otp=otp).order_by(PasswordReset.created_at.desc()).first()

        if password_reset:
            # Ensure that created_at is in UTC and offset-aware
            if password_reset.created_at.tzinfo is None:
                # If naive, make it UTC-aware
                password_reset.created_at = pytz.utc.localize(password_reset.created_at)

            # Debugging: Print the created_at and current time (in UTC)
            print(f"OTP created at (UTC): {password_reset.created_at}")
            print(f"Current time (UTC): {datetime.now(pytz.utc)}")

            # Check if OTP is within 10 minutes (600 seconds)
            time_diff = (datetime.now(pytz.utc) - password_reset.created_at).total_seconds()
            print(f"Time difference in seconds: {time_diff}")

            if time_diff < 600:
                user = User.query.get(password_reset.user_id)
                
                if user:
                    # Update the password
                    user.password = bcrypt.generate_password_hash(new_password)
                    db.session.commit()
                    
                    # Delete the OTP record after successful password reset
                    db.session.delete(password_reset)
                    db.session.commit()
                    
                    flash('Your password has been reset successfully!', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('User not found.', 'danger')
            else:
                flash('OTP has expired. Please request a new one.', 'danger')
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('otp_login.html')
