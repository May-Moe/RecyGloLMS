from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import app, db
from recyglolms.models import Upload
from flask_login import login_required, current_user
import os
from datetime import datetime

# Blueprint for file management
upload_bp = Blueprint('upload', __name__)

# Configure upload folder and allowed file types
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB


# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Route to view all files
@upload_bp.route('/files', methods=['GET'])
@login_required
def view_files():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    
    files = Upload.query.all()
    return render_template('view_files.html', files=files)


# Route to upload a new file
@upload_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash("Invalid file type or no file selected!", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure the directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])  # Create the 'static/uploads' folder if it doesn't exist

        file.save(filepath)

        new_upload = Upload(filename=filename, filetype=filename.rsplit('.', 1)[1].lower(), uploaddate=datetime.utcnow(), userid=current_user.userid)
        db.session.add(new_upload)
        db.session.commit()

        flash("File uploaded successfully!", "success")
        return redirect(url_for('upload.view_files'))

    return render_template('upload_file.html')


# Route to edit file metadata
@upload_bp.route('/edit/<int:uploadid>', methods=['GET', 'POST'])
@login_required
def edit_file(uploadid):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    file = Upload.query.get_or_404(uploadid)

    if request.method == 'POST':
        new_filename = request.form.get('filename')
        if new_filename:
            file.filename = secure_filename(new_filename)
            db.session.commit()
            flash("File information updated successfully!", "success")
            return redirect(url_for('upload.view_files'))

        flash("Filename cannot be empty!", "danger")

    return render_template('edit_file.html', file=file)


# Route to delete a file
@upload_bp.route('/delete/<int:uploadid>', methods=['POST'])
@login_required
def delete_file(uploadid):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    file = Upload.query.get_or_404(uploadid)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    # Remove file from storage
    if os.path.exists(filepath):
        os.remove(filepath)

    # Remove file from database
    db.session.delete(file)
    db.session.commit()
    flash("File deleted successfully!", "success")
    return redirect(url_for('upload.view_files'))