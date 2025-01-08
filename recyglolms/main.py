from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

# Create Blueprint for main routes
main_bp = Blueprint('main', __name__)

# Home route
@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')  # Render the home page template


# Example route for handling user uploads
@main_bp.route('/uploads')
@login_required
def uploads():
    # Fetch user uploads or other relevant data (placeholder for now)
    return render_template('uploads.html')