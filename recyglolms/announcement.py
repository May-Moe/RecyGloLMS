from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from recyglolms import db
from recyglolms.models import Announcement, Notification, User, ActionLog
from flask_login import login_required, current_user
import os
from datetime import datetime
from recyglolms.utils import upload_file_to_gcp  #  Import the new function for cloud storage
from recyglolms.utils import allowed_file
from google.cloud import storage


# Define allowed file extensions globally
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf'}

# Blueprint for announcements
announcement_bp = Blueprint('announcement', __name__)

# Configure upload folder and allowed extensions
# UPLOAD_FOLDER = os.path.join(app.root_path, 'static/announcements')
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg','pdf'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    """Check if the file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Route to view all announcements
@announcement_bp.route('/announcements', methods=['GET'])
@login_required
def view_all_announcements():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    
    announcements = Announcement.query.all()
    return render_template('viewallannouncement.html', announcements=announcements,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

@announcement_bp.route('/announcements_by_date/<string:date>', methods=['GET'])
@login_required
def get_announcements_by_date(date):
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        announcements = Announcement.query.filter(db.func.date(Announcement.event_date) == selected_date).all()

        announcement_list = [
            {"title": ann.title, "content": ann.content, "image": ann.announcement_img}
            for ann in announcements
        ]
        return {"announcements": announcement_list}, 200
    except ValueError:
        return {"error": "Invalid date format"}, 400


@announcement_bp.route('/add_announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        event_date_str = request.form.get('event_date')  # Get event date from form
        file = request.files.get('announcement_img')

        if not title or not content or not event_date_str:
            flash("Title, content, and event date are required!", "danger")
            return redirect(request.url)

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')  # Convert string to datetime
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(request.url)

        # ✅ Handle file upload with GCP
        file_url = None
        if file:
            file_url = upload_file_to_gcp(file, folder="announcements")  # Save to GCP storage

        # ✅ Create and save new announcement
        new_announcement = Announcement(
            title=title,
            content=content,
            announcement_img=file_url,  # Store URL instead of filename
            event_date=event_date,
            date=datetime.utcnow(),
            userid=current_user.userid
        )

        db.session.add(new_announcement)
        db.session.commit()

        # Create a notification for all users
        notification_message = f"New announcement: {title}"
        users = User.query.all()  # Get all users for notification
        for user in users:
            new_notification = Notification(
                message=notification_message,
                user_id=user.userid
            )
            db.session.add(new_notification)

        db.session.commit()

        flash("Announcement scheduled successfully and notifications sent!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('addannounce.html',
        current_user_name=current_user.name,
        current_user_email=current_user.email
    )
@announcement_bp.route('/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    announcement = Announcement.query.get_or_404(announcement_id)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        event_date_str = request.form.get('event_date')
        file = request.files.get('announcement_img')

        if not title or not content or not event_date_str:
            flash("Title, content, and event date are required!", "danger")
            return redirect(request.url)

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(request.url)

        # ✅ Upload new file to GCP if provided
        if file and allowed_file(file.filename):
            file_url = upload_file_to_gcp(file, folder="announcements")
            announcement.announcement_img = file_url  # Update to new file URL

        # ✅ Preserve old image if no new file
        # (no change to image URL if no file uploaded)

        announcement.title = title
        announcement.content = content
        announcement.event_date = event_date
        announcement.date = datetime.utcnow()

        db.session.commit()

        flash("Announcement updated successfully!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('editannouncement.html',
                           announcement=announcement,
                           current_user_name=current_user.name,
                           current_user_email=current_user.email)


@announcement_bp.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    announcement = Announcement.query.get_or_404(announcement_id)

    # ✅ Delete image from GCP Storage if exists
    if announcement.announcement_img:
        from urllib.parse import urlparse
        bucket_name = os.getenv("STORAGE_BUCKET", "sheworks-uploads")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Extract the file path from the URL
        parsed_url = urlparse(announcement.announcement_img)
        blob_path = parsed_url.path.lstrip('/')  # Remove leading slash

        blob = bucket.blob(blob_path)
        if blob.exists():
            blob.delete()

    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted successfully!", "success")
    return redirect(url_for('announcement.view_all_announcements'))

# @announcement_bp.route('/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
# @login_required
# def edit_announcement(announcement_id):
#     if not current_user.role:
#         flash("Unauthorized access!", "danger")
#         return redirect(url_for('auth.login'))

#     announcement = Announcement.query.get_or_404(announcement_id)

#     if request.method == 'POST':
#         title = request.form.get('title')
#         content = request.form.get('content')
#         event_date_str = request.form.get('event_date')
#         file = request.files.get('announcement_img')

#         if not title or not content or not event_date_str:
#             flash("Title, content, and event date are required!", "danger")
#             return redirect(request.url)

#         try:
#             event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
#         except ValueError:
#             flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
#             return redirect(request.url)

#         # If a new file is provided, update the image
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             announcement.announcement_img = filename
#         else:
#             # If no file is provided, preserve the existing image
#             filename = announcement.announcement_img

#         # Update the announcement
#         announcement.title = title
#         announcement.content = content
#         announcement.img = filename  # Ensure you're updating the right field
#         announcement.event_date = event_date
#         announcement.date = datetime.utcnow()

#         db.session.commit()

#         flash("Announcement updated successfully!", "success")
#         return redirect(url_for('announcement.view_all_announcements'))

#     return render_template('editannouncement.html',
#                             announcement=announcement,
#                             current_user_name=current_user.name,
#                             current_user_email=current_user.email)





# # Route to delete an announcement
# @announcement_bp.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
# @login_required
# def delete_announcement(announcement_id):
#     if not current_user.role:  # Ensure only admins can access
#         flash("Unauthorized access!", "danger")
#         return redirect(url_for('auth.login'))

#     announcement = Announcement.query.get_or_404(announcement_id)

#     # Delete the image file if it exists
#     if announcement.announcement_img:
#         image_path = os.path.join(app.config['UPLOAD_FOLDER'], announcement.announcement_img)
#         if os.path.exists(image_path):
#             os.remove(image_path)

#     # Delete the announcement
#     db.session.delete(announcement)
#     db.session.commit()

#     flash("Announcement deleted successfully!", "success")
#     return redirect(url_for('announcement.view_all_announcements'))