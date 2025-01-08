from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import app, db
from recyglolms.models import Announcement
from flask_login import login_required, current_user
import os
from datetime import datetime

# Blueprint for announcements
announcement_bp = Blueprint('announcement', __name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/announcements')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg','pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


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
    return render_template('viewallannouncement.html', announcements=announcements)


# Route to add a new announcement
@announcement_bp.route('/add_announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        file = request.files.get('announcement_img')

        if not title or not content:
            flash("Both title and content are required!", "danger")
            return redirect(request.url)

        # Handle file upload
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        elif file:
            flash("Invalid file format. Allowed formats: png, jpg, jpeg, gif", "danger")
            return redirect(request.url)

        # Create and save new announcement
        new_announcement = Announcement(
            title=title,
            content=content,
            announcement_img=filename,
            date=datetime.utcnow(),
            userid=current_user.userid
        )

        db.session.add(new_announcement)
        db.session.commit()

        flash("Announcement added successfully!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('addannounce.html')


# Route to edit an existing announcement
@announcement_bp.route('/edit_announcement/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    announcement = Announcement.query.get_or_404(announcement_id)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        file = request.files.get('announcement_img')

        if not title or not content:
            flash("Both title and content are required!", "danger")
            return redirect(request.url)

        # Handle file upload if a new file is provided
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            announcement.announcement_img = filename

        # Update the announcement
        announcement.title = title
        announcement.content = content
        announcement.date = datetime.utcnow()

        db.session.commit()

        flash("Announcement updated successfully!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('editannouncement.html', announcement=announcement)


# Route to delete an announcement
@announcement_bp.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    announcement = Announcement.query.get_or_404(announcement_id)

    # Delete the image file if it exists
    if announcement.announcement_img:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], announcement.announcement_img)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the announcement
    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted successfully!", "success")
    return redirect(url_for('announcement.view_all_announcements'))