from flask import Blueprint, render_template, request, redirect, url_for, flash
from recyglolms.__inti__ import db, bcrypt
from recyglolms.models import User
from flask_login import login_required, current_user

# Blueprint for admin functionality
admin_bp = Blueprint('admin', __name__)

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin, role=0 is user
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

# Route for adding a new user
@admin_bp.route('/adduser', methods=['GET', 'POST'])
@login_required
def add_user():
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', '0')  # Default to user (0)

        try:
            role = int(role)  # Convert role to integer safely
            if role not in [0, 1]:
                raise ValueError("Invalid role value")
        except ValueError:
            flash("Invalid role value. Must be 0 (user) or 1 (admin).", "danger")
            return render_template('adduser.html')

        # Check if the email already exists
        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "danger")
        else:
            # Hash the password and create a new user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(name=name, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully!", "success")
            return redirect(url_for('admin.dashboard'))

    return render_template('adduser.html')

# # Route to view all users
# @admin_bp.route('/users', methods=['GET'])
# @login_required
# def view_users():
#     # Ensure only admins can access
#     if not current_user.role:  # Assuming role=1 is admin
#         flash("Unauthorized access!", "danger")
#         return redirect(url_for('auth.login'))

#     users = User.query.all()  # Fetch all users
#     return render_template('users.html', users=users)