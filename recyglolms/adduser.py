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

# Route to view all users
@admin_bp.route('/viewallusers', methods=['GET'])
@login_required
def view_users():
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    users = User.query.all()  # Fetch all users
    return render_template('viewallusers.html', users=users)


# Route to edit a user
@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(user_id)  # Fetch user or return 404
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        role = request.form.get('role', '0')
        password = request.form['password']
        
        try:
            role = int(role)
            if role not in [0, 1]:
                raise ValueError("Invalid role value")
            user.role = role
        except ValueError:
            flash("Invalid role value. Must be 0 (user) or 1 (admin).", "danger")
            return render_template('edituser.html', user=user)

        # Check if the password is provided and hash it if necessary
        if password:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user.password = hashed_password

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for('admin.view_users'))

    return render_template('edituser.html', user=user)

# Route to delete a user
@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for('admin.view_users'))