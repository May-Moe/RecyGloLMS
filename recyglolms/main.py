from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from recyglolms.models import Activity, Course, Progress, Video, User, Module, Announcement
from recyglolms.__inti__ import db  # Assuming you're using SQLAlchemy

# Create Blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('login.html')  # Render home dashboard page

# Home route (Dashboard)
@main_bp.route('/home')
@login_required
def home():
    # Fetch all courses
    courses = Course.query.all()

    # Calculate progress for the current user in each course
    progress_data = {
        course.name: course.calculate_course_progress(current_user.userid) for course in courses
    }

    # Pass user and progress data to the template
    return render_template('home.html', user=current_user, progress_data=progress_data)
    # return render_template('home.html')  # Render home dashboard page

# View all activities route
@main_bp.route('/view_activities')
@login_required
def view_activities():
    activities = Activity.query.filter_by(userid=current_user.userid).all()  # Fetch user's activities
    return render_template('view_activities.html', activities=activities)

# Add activity route
@main_bp.route('/add_activity', methods=['GET', 'POST'])
@login_required
def add_activity():
    if request.method == 'POST':
        # Get the form data
        activity_name = request.form['activity_name']
        activity_description = request.form['activity_description']

        # Create a new Activity object with current date
        new_activity = Activity(
            name=activity_name,
            description=activity_description,
            date=datetime.utcnow(),  # Current date and time
            userid=current_user.userid  # Associate the activity with the logged-in user
        )

        # Add the activity to the database
        db.session.add(new_activity)
        db.session.commit()

        flash('Activity added successfully!', 'success')
        return redirect(url_for('main.view_activities'))  # Redirect to the view activities page

    return render_template('add_activity.html')  # Render the form template

@main_bp.route('/user/progress', methods=['GET'])
@login_required
def user_progress():
    # Fetch all courses
    courses = Course.query.all()

    # Calculate progress for the current user in each course
    progress_data = {
        course.name: course.calculate_course_progress(current_user.userid) for course in courses
    }

    # Pass user and progress data to the template
    return render_template('each_user_progress.html', user=current_user, progress_data=progress_data)



# Update video progress
@main_bp.route('/update_video_progress/<int:videoid>', methods=['POST'])
@login_required
def update_video_progress(videoid):
    progress = Progress.query.filter_by(userid=current_user.userid, videoid=videoid).first()

    if not progress:
        # If progress doesn't exist, create a new progress record
        progress = Progress(userid=current_user.userid, videoid=videoid)

    data = request.get_json()
    watched_duration = data.get('watched_duration', 0)

    video = Video.query.get(videoid)
    if not video:
        return jsonify({"error": "Video not found"}), 404

    # Ensure watched_duration is initialized if it's None
    if progress.watched_duration is None:
        progress.watched_duration = 0

    # Update the watched_duration
    progress.watched_duration += watched_duration

    # Check if the progress has reached or exceeded the video duration
    if progress.watched_duration >= video.duration:
        progress.completed = True
        progress.watched_duration = video.duration

    # Save the progress to the database
    db.session.add(progress)
    db.session.commit()

    return jsonify({"message": "Progress updated", "progress": progress.calculate_video_progress()}), 200

# Learning page with modules, courses, and video dropdowns
@main_bp.route('/learning', methods=['GET'])
@login_required
def learning_page():
    # Fetch all courses
    courses = Course.query.all()
    course_data = {}

    for course in courses:
        # For each course, fetch related modules
        modules = Module.query.filter_by(courseid=course.courseid).all()
        module_data = {}
        for module in modules:
            # For each module, fetch related videos
            videos = Video.query.filter_by(moduleid=module.moduleid).all()
            video_data = []
            for video in videos:
                video_data.append({
                    'videoid': video.videoid,
                    'title': video.title,
                    'url': video.url,
                    # Add other fields as necessary
                })
            module_data[module.name] = video_data
        course_data[course.name] = module_data

    return render_template('learning_page.html', course_data=course_data)