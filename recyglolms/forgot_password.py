# recyglolms/forgot_password.py
from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from app import app, db, mail
from flask_mail import Message
from models import User, PasswordReset
import random
import smtplib
from datetime import datetime, timedelta


def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not found!", "danger")
            return redirect(url_for('forgot_password'))

        # Generate and store OTP
        otp = generate_otp()
        reset_entry = PasswordReset(user_id=user.id, otp=otp)
        db.session.add(reset_entry)
        db.session.commit()

        # Send OTP via Email
        msg = Message("Your OTP for Login", recipients=[email])
        msg.body = f"Your OTP is {otp}. It is valid for 10 minutes."
        try:
            mail.send(msg)
            flash("An OTP has been sent to your email.", "success")
            return redirect(url_for('otp_login'))
        except smtplib.SMTPException:
            flash("Error sending email. Try again later.", "danger")

    return render_template('forgot_password.html')
