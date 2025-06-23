
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, send_from_directory
# from recyglolms.admin import allowed_file
from werkzeug.utils import secure_filename
from recyglolms import db
from recyglolms.models import Upload, User, ActionLog
from flask_login import login_required, current_user
import os
from datetime import datetime

# Blueprint for file management
upload_bp = Blueprint('upload', __name__)

# Configure upload folder and allowed file types
# UPLOAD_FOLDER = os.path.join(current_app.root_path, 'static', 'uploads')  # Absolute path
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'xz'}
# current_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# current_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16 MB

# Ensure the upload folder exists
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# Utility function to check allowed file types
# This version reads the allowed extensions from config safely
def allowed_file(filename):
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {
        'mp4', 'avi', 'mkv', 'mov', 'pdf', 'doc', 'docx', 'ppt', 'pptx',
        'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar', '7z',
        'tar', 'gz', 'tgz', 'bz2', 'xz'
    })
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

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

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], final_filename)

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
        # **Log the action**
        log_entry = ActionLog(
            userid=current_user.userid,
            username=current_user.name,  
            action_type="Add",
            target_table="Upload",
            target_id=new_upload.uploadid,
            timestamp=datetime.now(),
            details=f"Uploaded new file with the filename : {new_upload.filename}"
        )
        db.session.add(log_entry)
        db.session.commit()

        flash("File uploaded successfully!", "success")
        return redirect(url_for('upload.view_files'))

    return render_template('upload_file.html',
                           current_user_name = current_user.name,
                            current_user_email = current_user.email)

@upload_bp.route('/edit/<int:uploadid>', methods=['GET', 'POST'])
@login_required
def edit_file(uploadid):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    file = Upload.query.get_or_404(uploadid)
    original_filename = file.filename  # Store the original filename before any change
    changes = []  # Track changes made

    if request.method == 'POST':
        new_filename = request.form.get('filename')
        new_file = request.files.get('file')

        # Handle filename change first
        if new_filename and new_filename != file.filename:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            new_filename_secure = secure_filename(new_filename)
            new_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename_secure)

            if os.path.exists(old_filepath):
                os.rename(old_filepath, new_filepath)
                file.filename = new_filename_secure  # Update filename in DB
                changes.append(f"Filename changed from '{original_filename}' to '{new_filename_secure}'")

        # Handle file content replacement
        if new_file and allowed_file(new_file.filename):
            # Ensure we're saving to the correct path
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            new_file.save(file_path)
            changes.append(f"Replaced file contents for '{file.filename}'")

        db.session.commit()

        # Log the action
        if changes:
            log_entry = ActionLog(
                userid=current_user.userid,
                username=current_user.name,  
                action_type="Edit",
                target_table="Upload",
                target_id=file.uploadid,
                timestamp=datetime.now(),
                details="; ".join(changes)
            )
            db.session.add(log_entry)
            db.session.commit()

        flash("File information updated successfully!", "success")
        return redirect(url_for('upload.view_files'))

    return render_template('editfile.html', 
                           file=file,
                           current_user_name=current_user.name,
                           current_user_email=current_user.email)
# Delete file route
@upload_bp.route('/delete/<int:uploadid>', methods=['POST'])
@login_required
def delete_file(uploadid):
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    file = Upload.query.get_or_404(uploadid)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)

    # Remove file from storage
    if os.path.exists(filepath):
        os.remove(filepath)

    # Remove file from database
    db.session.delete(file)
    db.session.commit()

    # **Log the action**
    log_entry = ActionLog(
        userid=current_user.userid,
        username=current_user.name,  
        action_type="Delete",
        target_table="Upload",
        target_id=file.uploadid,
        timestamp=datetime.now(),
        details=f"Deleted file: {file.filename}"
    )
    db.session.add(log_entry)
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
        # Query to filter files based on search query and include associated user name
        files = db.session.query(Upload, User).join(User).filter(Upload.filename.ilike(f"%{search_query}%")).all()
    else:
        # Query to get all files with associated user names
        files = db.session.query(Upload, User).join(User).all()

    # Construct preview URLs
    for file, user in files:
        file.preview_url = url_for('upload.uploaded_file', filename=file.filename)

    return render_template('view_files.html', files=files,
                           current_user_name=current_user.name,
                           current_user_email=current_user.email)

@upload_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)