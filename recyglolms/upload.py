from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from recyglolms.__inti__ import app, db
from recyglolms.models import Upload
from flask_login import login_required, current_user
import os
from datetime import datetime

# Blueprint for file management
upload_bp = Blueprint('upload', __name__)

# Configure upload folder and allowed file types
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')  # Absolute path
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'xz'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to upload a new file
@upload_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        file = request.files.get('file')
        custom_name = request.form.get('filename')  # Get the user-specified filename

        if not file or not allowed_file(file.filename):
            flash("Invalid file type or no file selected!", "danger")
            return redirect(request.url)

        if not custom_name:
            flash("Custom file name is required!", "danger")
            return redirect(request.url)

        # Sanitize and append file extension to custom filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        sanitized_name = secure_filename(custom_name)
        final_filename = f"{sanitized_name}.{file_extension}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)

        # Save the file
        file.save(filepath)

        new_upload = Upload(
            filename=final_filename,
            filetype=file_extension,
            uploaddate=datetime.utcnow(),
            userid=current_user.userid
        )
        db.session.add(new_upload)
        db.session.commit()

        flash("File uploaded successfully!", "success")
        return redirect(url_for('upload.view_files'))

    return render_template('upload_file.html')


# Route to edit file metadata and replace file
@upload_bp.route('/edit/<int:uploadid>', methods=['GET', 'POST'])
@login_required
def edit_file(uploadid):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    file = Upload.query.get_or_404(uploadid)

    if request.method == 'POST':
        new_filename = request.form.get('filename')
        new_file = request.files.get('file')

        # Update file name
        if new_filename:
            old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(new_filename))
            
            # Rename file on disk if the filename has changed
            if old_filepath != new_filepath:
                os.rename(old_filepath, new_filepath)
                file.filename = secure_filename(new_filename)

        # Replace file content
        if new_file and allowed_file(new_file.filename):
            new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            new_file.save(new_filepath)

        db.session.commit()
        flash("File information updated successfully!", "success")
        return redirect(url_for('upload.view_files'))

    return render_template('editfile.html', file=file)

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

@upload_bp.route('/files', methods=['GET', 'POST'])
@login_required
def view_files():
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))
    
    search_query = request.form.get('search_query', '').strip()
    
    if search_query:
        files = Upload.query.filter(Upload.filename.ilike(f"%{search_query}%")).all()
    else:
        files = Upload.query.all()

    # Construct preview URLs
    for file in files:
        file.preview_url = url_for('upload.uploaded_file', filename=file.filename)

    return render_template('view_files.html', files=files)

@upload_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)