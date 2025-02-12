from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import db, bcrypt, app
from recyglolms.models import User, Course, Module, Video, Feedback
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os


# Blueprint for admin functionality
admin_bp = Blueprint('admin', __name__)
# Configure upload folder and allowed file types
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')  # Absolute path
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'xz'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Admin home page
@admin_bp.route('/admin_home')
@login_required
def admin_home():
    return render_template('admin_home.html')

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin, role=0 is user
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
     # Total number of users
    total_users = User.query.count()

    # Total users who haven't logged in for more than 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    inactive_users = User.query.filter((User.last_login == None) | (User.last_login < thirty_days_ago)).count()

    # Total number of courses
    total_courses = Course.query.count()  # Replace `Course` with your courses model

    # Total number of videos
    total_videos = Video.query.count()  # Replace `Video` with your videos model
    
    # Fetch courses and annotate them with their module count
    courses = Course.query.outerjoin(Module).group_by(Course).order_by(db.func.count(Module.moduleid).desc()).all()

    # Prepare course data with module counts for rendering
    course_data = [
        {
            'course_name': course.name,
            'module_count': len(course.modules),
            'description': course.description,
        }
        for course in courses
    ]
    
      # Get current date and calculate time thresholds
    now = datetime.utcnow()
    days_7 = now - timedelta(days=7)
    days_15 = now - timedelta(days=15)
    days_30 = now - timedelta(days=30)

    # Query users based on last login time
    active_7_days = User.query.filter(User.last_login >= days_7).count()
    active_15_days = User.query.filter(User.last_login >= days_15, User.last_login < days_7).count()
    active_30_days = User.query.filter(User.last_login >= days_30, User.last_login < days_15).count()
    inactive_30_days = User.query.filter(User.last_login < days_30).count()

    # Pass data to the template for rendering
    user_data = {
        'active_7_days': active_7_days,
        'active_15_days': active_15_days,
        'active_30_days': active_30_days,
        'inactive_30_days': inactive_30_days
    }
       
    current_user_name = current_user.name,
    current_user_email = current_user.email
    
    
    #Pass feedback data to the template
    feedbacks = db.session.query(Feedback, User).join(User).all()  # Fetch feedback with user details
  
    
    return render_template('dashboard.html',
        total_users=total_users,
        inactive_users=inactive_users,
        total_courses=total_courses,
        total_videos=total_videos,
        courses=course_data,
        user_data=user_data,
        current_user_name=current_user_name,
        current_user_email=current_user_email,
        feedbacks=feedbacks)

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
            new_user = User(name=name, email=email, password=hashed_password, role=role, last_login=datetime.now()) 
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

    users = User.query  # Base query for users

    # Handle POST requests
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()  # Get search query from the form
        inactivity_filter = request.form.get('inactivity_filter', '').strip()  # Get inactivity filter from dropdown
        sort_order = request.form.get('sort_order', 'desc')  # Get sort order (default: 'desc' for descending)

        # Filter by email if a search query is provided
        if search_query:
            users = users.filter(User.email.ilike(f'%{search_query}%'))

        # Filter by inactivity based on the selected option
        if inactivity_filter:
            days_map = {
                "0": 0,
                "7": 7,
                "15": 15,
                "30": 30,
            }
            days = days_map.get(inactivity_filter)
            if days:
                threshold_date = datetime.utcnow() - timedelta(days=days)
                users = users.filter((User.last_login == None) | (User.last_login < threshold_date))

        # Sorting by Last Login
        if sort_order == 'desc':
            users = users.order_by(User.last_login.desc())  # Sort by Last Login Descending
        else:
            users = users.order_by(User.last_login.asc())  # Sort by Last Login Ascending

    # Execute the query and fetch all users
    users = users.all()
    
    current_user_name = current_user.name,
    current_user_email = current_user.email

    return render_template('viewallusers.html', users=users, current_user_name=current_user_name, current_user_email=current_user_email)


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
        # change
        last_login=datetime.now(),
        
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
# Route to view all courses, modules, and videos
@admin_bp.route('/manage_course', methods=['GET'])
@login_required
def manage_course():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    courses = Course.query.all()
    modules = Module.query.all()
    videos = Video.query.all()

    return render_template('managecourse.html', courses=courses, modules=modules, videos=videos)


# Route to add a new course
@admin_bp.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('course_name')
        description = request.form.get('course_description')

        if not name or not description:
            flash("Course name and description are required.", "danger")
        else:
            new_course = Course(name=name, description=description, created_date=datetime.utcnow())
            db.session.add(new_course)
            db.session.commit()
            flash("Course added successfully!", "success")
            return redirect(url_for('admin.view_all'))

    return render_template('add_courses.html')


# Route to add a new module
@admin_bp.route('/add_module', methods=['GET', 'POST'])
@login_required
def add_module():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
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
            return redirect(url_for('admin.view_all'))

    courses = Course.query.all()  # Needed for module association
    return render_template('add_modules.html', courses=courses)


# Route to add a new video
@admin_bp.route('/add_video', methods=['GET', 'POST'])
@login_required
def add_video():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
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
            return redirect(url_for('admin.view_all'))

    modules = Module.query.all()  # Needed for video association
    return render_template('add_videos.html', modules=modules)

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

@admin_bp.route('/admin_feedback')
@login_required
def view_feedbacks():
    feedbacks = db.session.query(Feedback, User).join(User).all()  # Fetch feedback with user details
    return render_template('admin_feedback.html', feedbacks=feedbacks)


#Admin Activity page
@admin_bp.route('/Activity')
@login_required
def Activity():
    return render_template('Activity.html')