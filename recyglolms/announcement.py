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

        # Handle file upload
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Create and save new announcement
        new_announcement = Announcement(
            title=title,
            content=content,
            announcement_img=filename,
            event_date=event_date,
            date=datetime.utcnow(),
            userid=current_user.userid
        )

        db.session.add(new_announcement)
        db.session.commit()

        flash("Announcement scheduled successfully!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('addannounce.html')


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

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            announcement.announcement_img = filename

        # Update the announcement
        announcement.title = title
        announcement.content = content
        announcement.event_date = event_date
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