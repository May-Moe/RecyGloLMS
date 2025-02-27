from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import db, bcrypt, app
from recyglolms.models import User, Course, Module, Video, Feedback, Announcement
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

@admin_bp.route('/admin_home')
@login_required
def admin_home():
    # Fetch only the latest two announcements from the database
    announcements = Announcement.query.order_by(Announcement.date.desc()).limit(2).all()
    return render_template('admin_home.html', 
                           announcements=announcements,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

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

    return render_template('edituser.html', 
                           user=user,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

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

    return render_template('managecourse.html', 
                           courses=courses, modules=modules, videos=videos,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)


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
            return redirect(url_for('admin.manage_course'))

    return render_template('add_courses.html',
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)


@admin_bp.route('/add_module', methods=['GET', 'POST'])
@login_required
def add_module():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    courses = Course.query.all()  # Fetch all available courses

    if request.method == 'POST':
        print("Form Data:", request.form)  # Debugging to see if form data is received

        name = request.form.get('module_name')
        description = request.form.get('module_description')
        course_id = request.form.get('module_course_id')  # Match the form input name

        if not name or not description or not course_id:
            flash("Module name, description, and associated course are required.", "danger")
        else:
            new_module = Module(
                name=name,
                description=description,
                courseid=int(course_id),  # Ensure course_id is an integer
                created_date=datetime.utcnow()
            )
            db.session.add(new_module)
            db.session.commit()
            flash("Module added successfully!", "success")
            return redirect(url_for('admin.manage_course'))

    return render_template('add_modules.html', courses=courses)

@admin_bp.route('/add_video', methods=['GET', 'POST'])
@login_required
def add_video():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    # Get courses for the dropdown
    courses = Course.query.all()

    selected_course_id = request.form.get('course') or request.args.get('course')  # Retain course selection
    selected_module_id = request.form.get('module')
    modules = []

    if selected_course_id:
        try:
            selected_course_id = int(selected_course_id)  # Convert to int for correct comparison
            modules = Module.query.filter_by(courseid=selected_course_id).all()
        except ValueError:
            selected_course_id = None  # Reset if invalid

    if request.method == 'POST':
        title = request.form.get('video_title')
        url = request.form.get('video_url')
        duration = request.form.get('video_duration')

        if not title or not url or not duration or not selected_module_id:
            flash("All fields are required!", "danger")
        else:
            try:
                selected_module_id = int(selected_module_id)
                module = Module.query.get(selected_module_id)
                if not module:
                    flash("Invalid module selected!", "danger")
                    return redirect(url_for('admin.add_video'))

                new_video = Video(
                    title=title,
                    url=url,
                    duration=int(duration),
                    moduleid=selected_module_id
                )

                db.session.add(new_video)
                db.session.commit()
                flash("Video added successfully!", "success")
                return redirect(url_for('admin.manage_course'))

            except Exception as e:
                db.session.rollback()
                flash(f"Error adding video: {str(e)}", "danger")

    return render_template(
        'add_videos.html', 
        courses=courses, 
        modules=modules, 
        selected_course_id=selected_course_id, 
        selected_module_id=selected_module_id
    )
    
# Route to delete a course and its associated modules and videos
@admin_bp.route('/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    course = Course.query.get_or_404(course_id)

    try:
        # Delete all modules and videos associated with the course
        modules = Module.query.filter_by(courseid=course.courseid).all()
        for module in modules:
            Video.query.filter_by(moduleid=module.moduleid).delete()  # Delete associated videos
            db.session.delete(module)  # Delete module
        
        db.session.delete(course)  # Delete the course
        db.session.commit()
        flash("Course and its related modules and videos deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting course: {str(e)}", "danger")

    return redirect(url_for('admin.manage_course'))


# Route to delete a module and its associated videos
@admin_bp.route('/delete_module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(module_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    module = Module.query.get_or_404(module_id)

    try:
        # Delete all videos associated with the module
        Video.query.filter_by(moduleid=module.moduleid).delete()
        db.session.delete(module)
        db.session.commit()
        flash("Module and its related videos deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting module: {str(e)}", "danger")

    return redirect(url_for('admin.manage_course'))


# Route to delete a video
@admin_bp.route('/delete_video/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    video = Video.query.get_or_404(video_id)

    try:
        db.session.delete(video)
        db.session.commit()
        flash("Video deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting video: {str(e)}", "danger")

    return redirect(url_for('admin.manage_course'))

# Route to edit a course
@admin_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        course.name = request.form.get('course_name')
        course.description = request.form.get('course_description')

        if not course.name or not course.description:
            flash("Course name and description are required.", "danger")
        else:
            db.session.commit()
            flash("Course updated successfully!", "success")
            return redirect(url_for('admin.manage_course'))

    return render_template('edit_course.html', course=course)


# Route to edit a module
@admin_bp.route('/edit_module/<int:module_id>', methods=['GET', 'POST'])
@login_required
def edit_module(module_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    module = Module.query.get_or_404(module_id)
    courses = Course.query.all()  # Fetch all available courses

    if request.method == 'POST':
        module.name = request.form.get('module_name')
        module.description = request.form.get('module_description')
        module.courseid = int(request.form.get('module_course_id'))

        if not module.name or not module.description or not module.courseid:
            flash("Module name, description, and associated course are required.", "danger")
        else:
            db.session.commit()
            flash("Module updated successfully!", "success")
            return redirect(url_for('admin.manage_course'))

    return render_template('edit_module.html', module=module, courses=courses)


# Route to get modules for a selected course (used in AJAX request)
@admin_bp.route('/get_modules/<int:course_id>')
@login_required
def get_modules(course_id):
    modules = Module.query.filter_by(courseid=course_id).all()
    # Create the HTML options for the modules
    module_options = ""
    for module in modules:
        module_options += f'<option value="{module.moduleid}">{module.name}</option>'
    return module_options

# Route to edit a video
@admin_bp.route('/edit_video/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    video = Video.query.get_or_404(video_id)
    courses = Course.query.all()
    selected_course_id = video.module.courseid
    selected_module_id = video.moduleid
    modules = Module.query.filter_by(courseid=selected_course_id).all()

    if request.method == 'POST':
        selected_course_id = request.form.get('course_id')
        selected_module_id = request.form.get('module_id')

        video.title = request.form.get('video_title')
        video.url = request.form.get('video_url')
        video.duration = int(request.form.get('video_duration'))
        video.moduleid = int(selected_module_id)

        if not video.title or not video.url or not video.duration or not selected_module_id:
            flash("All fields are required!", "danger")
        else:
            db.session.commit()
            flash("Video updated successfully!", "success")
            return redirect(url_for('admin.manage_course'))

        # Update the modules list when the course changes
        modules = Module.query.filter_by(courseid=selected_course_id).all()

    return render_template('edit_video.html', video=video, courses=courses, modules=modules, 
                           selected_course_id=selected_course_id, selected_module_id=selected_module_id)


# Admin dashboard to view all user progress
@admin_bp.route('/view_all_progress', methods=['GET'])
@login_required
def view_all_progress():
    if not current_user.role:  # Ensure user is admin
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.home',))

    # Fetch all users
    users = User.query.filter_by(role=0).all()


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
    return render_template('view_all_progress.html', user_progress_data=user_progress_data, courses=courses,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

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

@admin_bp.route('/dashboard')
@login_required
def view_feedbacks():
    # feedbacks = db.session.query(Feedback, User).join(User).all()  # Fetch feedback with user details
    feedbacks = db.session.query(Feedback, User).join(User).order_by(Feedback.submit_date.desc()).limit(3).all()
    return render_template('dashboard.html', feedbacks=feedbacks)

@admin_bp.route('/admin_feedback')
@login_required
def admin_feedback():
    feedbacks = db.session.query(Feedback, User).join(User).all()  # Fetch feedback with user details
    # feedbacks = db.session.query(Feedback, User).join(User).order_by(Feedback.submit_date.desc()).limit(3).all()
    return render_template('admin_feedback.html', 
                           feedbacks=feedbacks,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

#Admin Activity page
@admin_bp.route('/Activity')
@login_required
def Activity():
    users = User.query.filter_by(role=0).all()  # Fetch all users from the database
    current_user_name = current_user.name,
    current_user_email = current_user.email
    return render_template('Activity.html', 
                           users=users,
                           current_user_name=current_user_name,
                           current_user_email=current_user_email)

#Admin Alumni page
@admin_bp.route('/Alumni_admin')
@login_required
def Alumni_admin():
    users = User.query.filter_by(role=0).all()  # Fetch all users from the database
    return render_template('Alumni_admin.html', 
                           users=users,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)