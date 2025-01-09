from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from recyglolms.__inti__ import db, bcrypt
from recyglolms.models import User, Course, Module, Video
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

@admin_bp.route('/viewallusers', methods=['GET', 'POST'])
@login_required
def view_users():
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    users = []  # Default empty list of users
    
    # Check if the request is a POST and if there is a search query
    if request.method == 'POST':
        search_query = request.form.get('search_query')  # Get the search query from the form
        if search_query:  # If search query is not empty, filter users by email
            users = User.query.filter(User.email.ilike(f'%{search_query}%')).all()
        else:  # If search query is empty (i.e., user deleted text), show all users
            users = User.query.all()
    else:
        # Default case: show all users when the page is first loaded
        users = User.query.all()

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

# Combined Management Route
@admin_bp.route('/manage_course', methods=['GET', 'POST'])
@login_required
def manage_course():
    # Ensure admin access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    # Handle form submissions
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'add_course':
            # Add a new course
            name = request.form.get('course_name')
            description = request.form.get('course_description')

            if not name or not description:
                flash("Course name and description are required.", "danger")
            else:
                new_course = Course(name=name, description=description, created_date=datetime.utcnow())
                db.session.add(new_course)
                db.session.commit()
                flash("Course added successfully!", "success")

        elif form_type == 'add_module':
            # Add a new module
            name = request.form.get('module_name')
            description = request.form.get('module_description')
            course_id = request.form.get('module_course_id')

            if not name or not description or not course_id:
                flash("Module name, description, and associated course are required.", "danger")
            else:
                new_module = Module(name=name, description=description, courseid=course_id, created_date=datetime.utcnow())
                db.session.add(new_module)
                db.session.commit()
                flash("Module added successfully!", "success")

        elif form_type == 'add_video':
            # Add a new video
            title = request.form.get('video_title')
            url = request.form.get('video_url')
            duration = request.form.get('video_duration')
            module_id = request.form.get('video_module_id')

            if not title or not url or not duration or not module_id:
                flash("Video title, URL, duration, and associated module are required.", "danger")
            else:
                new_video = Video(title=title, url=url, duration=duration, moduleid=module_id)
                db.session.add(new_video)
                db.session.commit()
                flash("Video added successfully!", "success")

        return redirect(url_for('admin.manage_course'))

    # Fetch existing data for rendering
    courses = Course.query.all()
    modules = Module.query.all()
    videos = Video.query.all()

    return render_template('managecourse.html', courses=courses, modules=modules, videos=videos)
# Admin dashboard to view all user progress
@admin_bp.route('/view_all_progress', methods=['GET'])
@login_required
def view_all_progress():
    if not current_user.role:  # Ensure user is admin
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.home'))

    # Fetch all users
    users = User.query.all()

    # Create a dictionary to store progress for each user
    user_progress_data = {}

    for user in users:
        # For each user, get all courses and calculate progress
        courses = Course.query.all()
        progress_data = {}

        # Iterate through courses to get progress data for each course
        for course in courses:
            # Calculate the progress for the user for this particular course
            progress_percentage = course.calculate_course_progress(user.userid)
            progress_data[course.name] = progress_percentage

        user_progress_data[user.userid] = {
            'name': user.name,
            'progress': progress_data
        }

    # Pass all users' progress to the template
    return render_template('view_all_progress.html', user_progress_data=user_progress_data, courses=courses)

# View progress of a specific user
@admin_bp.route('/user_progress/<int:userid>', methods=['GET'])
@login_required
def user_progress(userid):
    if not current_user.role:
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.home'))

    user = User.query.get_or_404(userid)
    courses = Course.query.all()

    progress_data = {
        course.name: course.calculate_course_progress(user.userid) for course in courses
    }

    return render_template('each_user_progress.html', user=user, progress_data=progress_data)

