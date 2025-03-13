import os
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from recyglolms.models import Course, Video, Progress, Activity, Module, User, Feedback, ActivityImage, Announcement, CourseClass, UserClass, Class, Notification
from recyglolms.__inti__ import db, app, bcrypt

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('login.html')

@main_bp.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    # Get the user's assigned class IDs
    user_classes = [uc.classid for uc in UserClass.query.filter_by(userid=current_user.userid).all()]
    
    # Get courses linked to those classes
    courses = Course.query.join(CourseClass).filter(CourseClass.classid.in_(user_classes)).all()

    # Compute progress for filtered courses
    progress_data = {
        course.name: course.calculate_course_progress(current_user.userid) for course in courses
    }

    if request.method == 'POST':  # Handle username update
        new_username = request.form.get('username')
        if new_username:  # Validate the input
            current_user.name = new_username
            db.session.commit()  # Save the change to the database
            flash("Username updated successfully!", "success")
            return redirect(url_for('main.home'))  # Redirect to home

    # Pass current user info to the template
    current_username = current_user.name
    current_useremail = current_user.email

    return render_template(
        'home.html',
        courses=courses,
        progress_data=progress_data,
        current_username=current_username,
        current_useremail=current_useremail,
        current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None
    )
# Ensure the upload folder exists
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


        

# New route to view a specific activity by its ID
@main_bp.route('/user_activity/view/<int:activity_id>', methods=['GET'])
@login_required
def view_activity(activity_id):
    # Fetch the specific activity based on the ID
    activity = Activity.query.filter_by(activityid=activity_id, userid=current_user.userid).first()
    # Pass current user info to the template
    current_username = current_user.name
    current_useremail = current_user.email

    if activity:
        # Fetch all images related to this activity
        images = [img.activity_image for img in ActivityImage.query.filter_by(activityid=activity.activityid).all()]

        # Return the activity data as JSON (or render a template if needed)
        return jsonify({
            "activityid": activity.activityid,
            "name": activity.name,
            "description": activity.description,
            "images": images,
            "current_user_name": current_username,
            "current_user_email": current_useremail
            
        })
    else:
        return jsonify({"error": "Activity not found"}), 404

@main_bp.route('/user_activity', methods=['GET', 'POST'])
@login_required
def user_activity():
    if request.method == 'POST':
        # Handle POST requests to create a new activity
        activity_name = request.form.get('activity_name')
        activity_description = request.form.get('activity_description')
        images = request.files.getlist('activity_images')

        if not activity_name or not activity_description:
            return jsonify({"error": "Activity name and description are required!"}), 400

        new_activity = Activity(
            name=activity_name,
            description=activity_description,
            date=datetime.utcnow(),
            userid=current_user.userid
        )
        db.session.add(new_activity)
        db.session.commit()

        uploaded_images = []
        for file in images:
            if file and allowed_file(file.filename):
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                sanitized_name = secure_filename(file.filename.rsplit('.', 1)[0])
                final_filename = f"{sanitized_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{file_extension}"
                filepath = os.path.join(UPLOAD_FOLDER, final_filename)
                file.save(filepath)

                new_image = ActivityImage(activityid=new_activity.activityid, activity_image=final_filename)
                db.session.add(new_image)
                uploaded_images.append(final_filename)

        db.session.commit()

        return jsonify({
            "activityid": new_activity.activityid,
            "name": new_activity.name,
            "description": new_activity.description,
            "images": uploaded_images
        }), 201

    # GET request: Fetch activities for the logged-in user
    activities = Activity.query.filter_by(userid=current_user.userid).all()

    activity_list = []
    for activity in activities:
        images = [img.activity_image for img in ActivityImage.query.filter_by(activityid=activity.activityid).all()]
        activity_list.append({
            "activityid": activity.activityid,
            "name": activity.name,
            "description": activity.description,
            "images": images
        })

    # Ensure the server sends JSON when requested by AJAX
    if 'application/json' in request.headers.get('Accept', ''):
        return jsonify(activity_list)

    # For non-AJAX requests, render the HTML template
    return render_template('user_activity.html', activities=activity_list,
                                                       current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)



@main_bp.route('/user_activity/<int:activity_id>', methods=['DELETE'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    return '', 204

@main_bp.route('/learning')
@login_required
def learning():
    # Fetch classes where the current user is assigned
    user_classes = Class.query.join(UserClass).filter(UserClass.userid == current_user.userid).all()
    
    return render_template('learning_classes.html',
                            classes=user_classes,  # Pass the correct classes to the template
                            current_user_name=current_user.name,
                            current_user_email=current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)

@main_bp.route('/learning/class/<int:classid>')
@login_required
def learning_class_courses(classid):
    # Fetch the selected class
    selected_class = Class.query.get_or_404(classid)

    # Fetch only the unique courses associated with the selected class
    courses = Course.query.join(CourseClass).filter(CourseClass.classid == classid).distinct().all()

    # Debugging output to check for duplicates
    print("Fetched Unique Courses:", [(course.courseid, course.name) for course in courses])

    return render_template('learning_page.html',
                            selected_class=selected_class,
                            courses=courses,
                            current_user_name=current_user.name,
                            current_user_email=current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)
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
                            current_user_email = current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)

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




UPLOAD_FOLDER_PROFILE = os.path.join(app.root_path, 'static/profile_images')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER_PROFILE'] = UPLOAD_FOLDER_PROFILE

if not os.path.exists(UPLOAD_FOLDER_PROFILE):
    os.makedirs(UPLOAD_FOLDER_PROFILE)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/user_account', methods=['GET'])
@login_required
def user_account():
    return render_template(
        'user_account.html',
        current_user_name=current_user.name,
        current_user_email=current_user.email,
        current_user_id=current_user.userid,
        current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None
    )

@app.route('/update_profile_image', methods=['POST'])
@login_required
def update_profile_image():
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER_PROFILE, filename)
            try:
                file.save(file_path)
                print(f"File successfully saved at: {file_path}")

                # Update the user's profile image in the database
                current_user.profile_img = f'profile_images/{filename}'  # Store relative path to static
                db.session.commit()
                flash("Profile image updated successfully!", "success")
            except Exception as e:
                print(f" Error saving file: {e}")
                flash("File upload failed!", "danger")
        else:
            flash("Invalid file format!", "danger")
    return redirect(url_for('user_account'))

@app.route('/update_username', methods=['POST'])
@login_required
def update_username():
    new_username = request.form.get('username')
    if new_username:
        current_user.name = new_username
        db.session.commit()
        flash("Username updated successfully!", "success")
    return redirect(url_for('user_account'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current-password')
    new_password = request.form.get('new-password')
    if current_password and new_password:
        if bcrypt.check_password_hash(current_user.password, current_password):
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            current_user.password = hashed_password
            db.session.commit()
            flash("Password updated successfully!", "success")
        else:
            flash("Current password is incorrect.", "danger")
    return redirect(url_for('user_account'))
    
#for user feedback

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

    # Fetch users with their enrolled classes
    users_with_classes = []
    for user in users:
        enrolled_classes = [uc.class_ for uc in user.classes]  # Get class objects
        users_with_classes.append({'user': user, 'classes': enrolled_classes})

    return render_template('Alumni_user.html', 
                           users=users,
                           users_with_classes=users_with_classes,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)
    
@app.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_as_read():
    Notification.query.filter_by(user_id=current_user.userid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})

@app.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.userid, is_read=False).order_by(Notification.created_at.desc()).all()
    
    notification_list = [{"id": n.id, "message": n.message, "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")} for n in notifications]
    
    return jsonify({"notifications": notification_list, "count": len(notification_list)})

