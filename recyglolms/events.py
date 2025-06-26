from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from recyglolms import db
from recyglolms.models import Event, User, ActionLog
from flask_login import login_required, current_user
import os
from datetime import datetime
from recyglolms.utils import upload_file_to_gcp, allowed_file

events_bp = Blueprint('events', __name__)

# View all events
@events_bp.route('/events')
@login_required
def show_events():
    now = datetime.utcnow()
    upcoming_events = Event.query.filter(Event.event_date >= now).order_by(Event.event_date.asc()).all()
    past_events = Event.query.filter(Event.event_date < now).order_by(Event.event_date.desc()).all()
    return render_template('events.html', title="Events", upcoming_events=upcoming_events, past_events=past_events)

# Add event
@events_bp.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if current_user.role == 0:  # Only admins/sub-admins allowed
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        location = request.form['location']
        image = request.files.get('image')

        if not title or not description or not event_date:
            flash("Title, description, and event date are required!", "danger")
            return redirect(request.url)

        image_url = upload_file_to_gcp(image, 'events') if image and allowed_file(image.filename) else None

        new_event = Event(
            title=title,
            description=description,
            event_date=datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S'),
            location=location,
            image_url=image_url,
            user_id=current_user.userid
        )
        db.session.add(new_event)
        db.session.commit()

        # Log the action
        log_entry = ActionLog(
            userid=current_user.userid,
            username=current_user.name,
            action_type="Add",
            target_table="Event",
            target_id=new_event.id,
            timestamp=datetime.now(),
            details=f"Added new event: {new_event.title}"
        )
        db.session.add(log_entry)
        db.session.commit()

        flash("Event added successfully!", "success")
        return redirect(url_for('events.show_events'))
    return render_template('event_form.html', title="Add Event")

# Edit event
@events_bp.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.role == 0:  # Only admins/sub-admins allowed
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d %H:%M:%S')
        event.location = request.form['location']
        image = request.files.get('image')
        if image and allowed_file(image.filename):
            event.image_url = upload_file_to_gcp(image, 'events')
        db.session.commit()

        # Log the action
        log_entry = ActionLog(
            userid=current_user.userid,
            username=current_user.name,
            action_type="Edit",
            target_table="Event",
            target_id=event.id,
            timestamp=datetime.now(),
            details=f"Edited event: {event.title}"
        )
        db.session.add(log_entry)
        db.session.commit()

        flash("Event updated successfully!", "success")
        return redirect(url_for('events.show_events'))
    return render_template('event_form.html', title="Edit Event", event=event)

# Delete event
@events_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if current_user.role == 0:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    db.session.delete(event)
    db.session.commit()

    # Log the action
    log_entry = ActionLog(
        userid=current_user.userid,
        username=current_user.name,
        action_type="Delete",
        target_table="Event",
        target_id=event.id,
        timestamp=datetime.now(),
        details=f"Deleted event: {event.title}"
    )
    db.session.add(log_entry)
    db.session.commit()

    flash("Event deleted successfully!", "success")
    return redirect(url_for('events.show_events'))