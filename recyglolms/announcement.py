from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import app, db
from recyglolms.models import Upload
from flask_login import login_required, current_user
import os
from datetime import datetime
from recyglolms.models import Announcement

# Blueprint for announcements
announcement_bp = Blueprint('announcement', __name__)

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

        if not title or not content:
            flash("Both title and content are required!", "danger")
            return redirect(request.url)

        # Create and save new announcement
        new_announcement = Announcement(
            title=title,
            content=content,
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

        if not title or not content:
            flash("Both title and content are required!", "danger")
            return redirect(request.url)

        # Update the announcement
        announcement.title = title
        announcement.content = content
        announcement.date_posted = datetime.utcnow()

        db.session.commit()

        flash("Announcement updated successfully!", "success")
        return redirect(url_for('announcement.view_all_announcements'))

    return render_template('editannounce.html', announcement=announcement)

# Route to delete an announcement
@announcement_bp.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    announcement = Announcement.query.get_or_404(announcement_id)

    # Delete the announcement
    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted successfully!", "success")
    return redirect(url_for('announcement.view_all_announcements'))