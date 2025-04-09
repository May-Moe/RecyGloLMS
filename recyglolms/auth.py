import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import Blueprint, render_template, request, redirect, url_for, flash
from recyglolms import db, bcrypt
from recyglolms.models import PasswordReset, User
from flask_login import login_user, logout_user, login_required, current_user
from flask import current_app
from flask_mail import Message  # ✅ Correct one
import pytz

from datetime import datetime, timedelta, timezone

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
            
            # Set OTP expiration time (e.g., 10 minutes)
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=1)

            # Save the OTP to the PasswordReset model
            password_reset = PasswordReset(
                user_id=user.userid, 
                otp=otp, 
                created_at=datetime.now(timezone.utc), 
                expiration_time=expiration_time
            )
            db.session.add(password_reset)
            db.session.commit()

            # Temporarily bypass email sending
            # msg = Message(
            #     subject="Password Reset OTP",
            #     recipients=[email],
            #     body=f"Your OTP for password reset is: {otp}"
            # )
            # mail.send(msg)  # This line is commented out to avoid the email sending error
            
            # ✅ Send the OTP via SendGrid
            send_status = send_otp_email(email, otp)
            if send_status == 202:
                flash('OTP sent to your email. Please check your inbox.', 'success')
            else:
                flash('Failed to send OTP email. Please try again later.', 'danger')
                return redirect(url_for('auth.forgot_password'))

            
            # Redirect directly to the OTP verification page
            flash('OTP generated. Please proceed to verify your OTP.', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('Email address not found. Please check and try again.', 'danger')
    
    return render_template('forgot_password.html')


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

        # Fetch the most recent password reset record for the given OTP
        password_reset = PasswordReset.query.filter_by(otp=otp).order_by(PasswordReset.created_at.desc()).first()

        if password_reset:
            # Ensure that created_at is in UTC and offset-aware
            if password_reset.created_at.tzinfo is None:
                # If naive, make it UTC-aware
                password_reset.created_at = pytz.utc.localize(password_reset.created_at)

            # Ensure expiration_time is in UTC and offset-aware
            if password_reset.expiration_time.tzinfo is None:
                # If naive, make it UTC-aware
                password_reset.expiration_time = pytz.utc.localize(password_reset.expiration_time)

            # Debugging: Print the created_at and current time (in UTC)
            print(f"OTP created at (UTC): {password_reset.created_at}")
            print(f"Current time (UTC): {datetime.now(timezone.utc)}")

            if datetime.now(timezone.utc) <= password_reset.expiration_time:
                user = User.query.get(password_reset.user_id)

                if user:
                    # Update password
                    user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                    db.session.commit()

                    # Delete OTP
                    db.session.delete(password_reset)
                    db.session.commit()

                    flash('Your password has been reset successfully!', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('User not found.', 'danger')
            else:
                db.session.delete(password_reset)
                db.session.commit()
                flash('OTP has expired. Please request a new one.', 'danger')

        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('otp_login.html')


def send_otp_email(email, otp):
    """Send OTP email using SendGrid with HTML formatting."""
    sg = SendGridAPIClient(api_key=current_app.config['SENDGRID_API_KEY'])

    # HTML Content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px; background-color: #f4f4f4;">
        <div style="max-width: 500px; margin: auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0px 0px 10px #ccc;">
            <h2 style="color: #2C3E50;">Password Reset Request</h2>
            <p style="font-size: 16px;">You have requested to reset your password. Please use the following OTP to proceed:</p>
            <h3 style="font-size: 22px; color: #E74C3C; padding: 10px; background: #f9eceb; display: inline-block; border-radius: 5px;">{otp}</h3>
            <p style="font-size: 14px; color: #7f8c8d;">This OTP will expire in 10 minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
            <hr style="border: 0.5px solid #ddd;">
        </div>
    </body>
    </html>
    """

    message = Mail(
        from_email=current_app.config['MAIL_DEFAULT_SENDER'],
        to_emails=email,
        subject="Your OTP for Password Reset",
        plain_text_content=f"Your OTP for password reset is: {otp}\n\nThis OTP will expire in 10 minutes.",
        html_content=html_content  # Adding the HTML version
    )

    try:
        response = sg.send(message)
        return response.status_code  # Should return 202 if successful
    except Exception as e:
        print("Email sending failed:", str(e))
        return None


# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
# import os
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail

# message = Mail(
#     from_email='contact@sanaterra.info',
#     to_emails='chrisrecyglo@gmail.com',
#     subject='Sending with Twilio SendGrid is Fun',
#     html_content='<strong>and easy to do anywhere, even with Python</strong>')
# try:
#     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#     response = sg.send(message)
#     print(response.status_code)
#     print(response.body)
#     print(response.headers)
# except Exception as e:
#     print(e.message)