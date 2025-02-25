from asyncio import current_task
import os
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from recyglolms.models import Course, Video, Progress, Activity, Module, User, Feedback, ActivityImage, Announcement
from recyglolms.__inti__ import db, app

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
# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/add_activity', methods=['GET', 'POST'])
@login_required
def add_activity():
    if request.method == 'POST':
        try:
            activity_name = request.form.get('activity_name')
            activity_description = request.form.get('activity_description')
            images = request.files.getlist('activity_images')  # Multiple images

            if not activity_name or not activity_description:
                flash("Activity name and description are required!", "danger")
                return redirect(request.url)

            # Step 1: Create and flush the new activity to get the activityid
            new_activity = Activity(
                name=activity_name,
                description=activity_description,
                date=datetime.utcnow(),
                userid=current_user.userid
            )
            db.session.add(new_activity)
            db.session.flush()  # Get the generated activityid before committing

            uploaded_images = 0
            for file in images:
                if not file or not allowed_file(file.filename):
                    flash(f"Invalid file type or no file selected for {file.filename}!", "danger")
                    continue

                # Generate secure filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                sanitized_name = secure_filename(file.filename.rsplit('.', 1)[0])  # Remove extension
                final_filename = f"{sanitized_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{file_extension}"

                filepath = os.path.join(UPLOAD_FOLDER, final_filename)

                # Save the file
                file.save(filepath)

                # Step 2: Save image reference in activity_image table
                new_image = ActivityImage(activityid=new_activity.activityid, activity_image=final_filename)
                db.session.add(new_image)
                uploaded_images += 1

            # Step 3: Commit everything
            db.session.commit()

            flash(f"Activity added successfully with {uploaded_images} images!", "success")
            return redirect(url_for('main.view_activities'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(request.url)

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
    return render_template('learning_page.html',
                            courses=courses,
                            current_user_name = current_user.name,
                            current_user_email = current_user.email)

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
    return render_template('course_detail.html', 
                           data=data,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

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
    return render_template('each_user_progress.html', user=current_user, progress_data=progress_data, courses=courses
                           ,current_user_name = current_user.name,
                            current_user_email = current_user.email)


@main_bp.route('/user_home')
@login_required
def user_home():
    # Fetch only the latest two announcements from the database
    announcements = Announcement.query.order_by(Announcement.date.desc()).limit(2).all()
    return render_template('user_home.html', announcements=announcements,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)



@main_bp.route('/user_account', methods=['GET', 'POST'])
@login_required
def user_account():
    return render_template(
        'user_account.html',
        current_user_name=current_user.name,  
        current_user_email=current_user.email,
        current_user_id=current_user.userid 
    )



#for user feedback

# Feedback Submission Route
@main_bp.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    feedback_text = request.form.get('message')

    if not feedback_text:
        flash("Feedback cannot be empty.", "danger")
        return redirect(url_for('main.user_home'))

    # Create a new Feedback record
    new_feedback = Feedback(
        userid=current_user.userid,
        feedback=feedback_text,
        submit_date=datetime.utcnow()
    )

    db.session.add(new_feedback)
    db.session.commit()
    flash("Thank you for your feedback!", "success")

    return redirect(url_for('main.user_home'))

@main_bp.route('/Alumni_user')
@login_required
def Alumni_user():
    users = User.query.filter_by(role=0).all()  # Fetch all users from the database
    return render_template('Alumni_user.html', 
                           users=users,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)