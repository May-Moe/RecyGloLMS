from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from recyglolms.models import Course, Video, Progress, Activity, Module, User
from recyglolms.__inti__ import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('login.html')

@main_bp.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    courses = Course.query.all()
    progress_data = {
        course.name: course.calculate_course_progress(current_user.userid) for course in courses
    }

    if request.method == 'POST':  # Handle username update
        new_username = request.form.get('username')
        if new_username:  # Validate the input
            current_user.name = new_username
            db.session.commit()  # Save the change to the database
            flash("Username updated successfully!", "success")
            return redirect(url_for('main.home'))  # Corrected endpoint name

    # Pass current user info to the template
    current_username = current_user.name
    current_useremail = current_user.email

    return render_template(
        'home.html',
        courses=courses,
        progress_data=progress_data,
        current_username=current_username,
        current_useremail=current_useremail
    )


# Add activity route
@main_bp.route('/add_activity', methods=['GET', 'POST'])
@login_required
def add_activity():
    if request.method == 'POST':
        activity_name = request.form['activity_name']
        activity_description = request.form['activity_description']

        new_activity = Activity(
            name=activity_name,
            description=activity_description,
            date=datetime.utcnow(),
            userid=current_user.userid
        )

        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
        return redirect(url_for('main.view_activities'))

    return render_template('add_activity.html')

# View activities
@main_bp.route('/view_activities')
@login_required
def view_activities():
    activities = Activity.query.filter_by(userid=current_user.userid).all()
    return render_template('view_activities.html', activities=activities)

@main_bp.route('/learning')
@login_required
def learning():
    courses = Course.query.all()
    return render_template('learning_page.html', courses=courses)

@main_bp.route('/course/<int:courseid>')
@login_required
def course_detail(courseid):
    course = Course.query.get_or_404(courseid)
    modules = Module.query.filter_by(courseid=courseid).all()

    # Transform URLs to embeddable format
    for module in modules:
        for video in module.videos:
            if 'youtu.be/' in video.url:
                # Extract video ID and create the embeddable URL
                video_id = video.url.split('/')[-1]
                video.url = f'https://www.youtube.com/embed/{video_id}'
            elif 'youtube.com/watch?v=' in video.url:
                # Handle full YouTube URLs
                video.url = video.url.replace('watch?v=', 'embed/')

    data = {
        "course": course,
        "modules": [
            {
                "module": module,
                "videos": module.videos,
                "quizzes": module.quizzes  # Include quizzes for each module
            } for module in modules
        ]
    }
    return render_template('course_detail.html', data=data)

@main_bp.route('/update_video_progress/<int:videoid>', methods=['POST'])
@login_required
def update_video_progress(videoid):
    """
    Update the progress of a video for the current user when they click on it.
    """
    print(f"Received progress update for video ID: {videoid}")  # Debugging line
    
    # Fetch the video
    video = Video.query.get(videoid)
    if not video:
        return jsonify({"error": "Video not found"}), 404

    # Fetch or create progress record for the user
    progress = Progress.query.filter_by(userid=current_user.userid, videoid=videoid).first()
    if not progress:
        progress = Progress(userid=current_user.userid, videoid=videoid, watched_duration=0, completed=False)

    # Parse the JSON body
    data = request.get_json()
    completed = data.get('completed', False)  # Check if the request is marking the video as complete

    if completed:
        # Mark as complete directly
        progress.watched_duration = video.duration
        progress.completed = True
    else:
        # Handle incremental updates (if needed)
        increment_value = data.get('increment', 0)
        print(f"Increment value: {increment_value}")  # Debugging log

        progress.watched_duration = min(progress.watched_duration + increment_value, video.duration)
        progress.completed = progress.watched_duration >= video.duration

    # Save progress
    db.session.add(progress)
    db.session.commit()

    # Calculate module and course progress
    module_progress = video.module.calculate_module_progress(current_user.userid)
    course_progress = video.module.course.calculate_course_progress(current_user.userid)

    # Debugging log for progress values
    print(f"Module Progress: {module_progress}, Course Progress: {course_progress}")

    return jsonify({
        "message": "Progress updated successfully",
        "module_progress": module_progress,
        "course_progress": course_progress
    })
@main_bp.route('/user/progress', methods=['GET'])
@login_required
def user_progress():
    courses = Course.query.all()
    progress_data = {
        course.name: course.calculate_course_progress(current_user.userid) for course in courses
    }
    return render_template('each_user_progress.html', user=current_user, progress_data=progress_data)


#for user_home
@main_bp.route('/user_home')
@login_required
def user_home():
    return render_template('user_home.html')

#for user_account
@main_bp.route('/user_account')
@login_required
def user_account():
    return render_template('user_account.html')
