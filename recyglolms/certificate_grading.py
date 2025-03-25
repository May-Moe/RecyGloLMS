from datetime import date, datetime
from flask import Blueprint, request, jsonify, render_template, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from recyglolms.__inti__ import db
from recyglolms.models import Assese_Response, UserResponse, Certificate, User, Assese_Questions, Assessment, UserClass, Class, Quiz, UserResponse, UserResponse
from sqlalchemy.sql import func
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import send_file
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import landscape

grading_bp = Blueprint('grading', __name__)


from sqlalchemy.sql import func

# Function to calculate the final grade
def calculate_final_grade(user_id, class_id):
    """Calculate the user's final grade based on quiz and assessment scores for a specific class."""
    
    # Fetch total marks for the user and assessment within the given class
    assessment_score = db.session.query(
        func.coalesce(func.sum(Assese_Response.marks), 0)
    ).join(
        Assese_Questions, Assese_Response.question_id == Assese_Questions.id
    ).join(
        Assessment, Assese_Questions.assessment_id == Assessment.id
    ).filter(
        Assese_Response.user_id == user_id,
        Assessment.classid == class_id
    ).scalar()

    if assessment_score is None:
        assessment_score = 0

    # Fetch all user responses and the most recent quiz scores
    user_responses = db.session.query(UserResponse) \
        .filter(UserResponse.userid == user_id) \
        .join(Quiz, Quiz.quizid == UserResponse.quizid) \
        .filter(Quiz.moduleid == class_id) \
        .order_by(UserResponse.created_date.desc()) \
        .all()

      # Fetch the latest quiz score for the user (using max to ensure we get the latest quiz)
    user_responses = db.session.query(UserResponse.quizid, func.max(UserResponse.created_date).label('latest_date'))\
                               .filter(UserResponse.userid == user_id)\
                               .group_by(UserResponse.quizid).subquery()

    average_quiz_score = db.session.query(func.coalesce(func.avg(UserResponse.score), 0))\
                                   .filter(UserResponse.userid == user_id,
                                           UserResponse.quizid == user_responses.c.quizid,
                                           UserResponse.created_date == user_responses.c.latest_date)\
                                   .scalar()

    # Debugging the quiz score
    print(f"User ID: {user_id}, Retrieved Average Quiz Score: {average_quiz_score}")

    # If no quiz score found, default it to 0
    if average_quiz_score is None:
        average_quiz_score = 0

    # Calculate final score as average of quiz and assessment scores
    final_score = (average_quiz_score + assessment_score) / 2

    # Return separate quiz_score, assessment_score, and final_score
    return average_quiz_score, assessment_score, final_score

# API to fetch grade for a specific user
@grading_bp.route('/api/get-grade/<int:user_id>', methods=['GET'])
@login_required
def get_grade(user_id):
    """Fetches and returns the calculated grade for the given user."""
    
    quiz_id = request.args.get("quiz_id", type=int) or None
    assessment_id = request.args.get("assessment_id", type=int) or None

    if quiz_id is None or assessment_id is None:
        return jsonify({"error": "Quiz ID and Assessment ID are required!"}), 400

    final_score, grade = calculate_final_grade(user_id, quiz_id, assessment_id)

    return jsonify({
        "user_id": user_id,
        "quiz_score": final_score,  # Fixed JSON key
        "grade": grade
    })
    
# Admin panel to display all users' grades with class information
@grading_bp.route('/admin/grading', methods=['GET'])
@login_required
def admin_gradebook():
    """Displays all users' grades in the admin panel, grouped by class."""
    
    # Check if the user has admin privileges
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    users = User.query.all()
    all_grades = []

    # Loop through each user to calculate and collect grades
    for user in users:
        # Fetch the user's classes
        user_classes = db.session.query(Class).join(UserClass).filter(UserClass.userid == user.userid).all()

        for user_class in user_classes:
            # Fetch the UserClass entry to get is_access_granted
            user_class_entry = UserClass.query.filter_by(userid=user.userid, classid=user_class.classid).first()

            # Ensure we have a valid UserClass entry before accessing is_access_granted
            is_access_granted = user_class_entry.is_access_granted if user_class_entry else False

            # Calculate quiz, assessment, and final scores for each class
            average_quiz_score, assessment_score, final_score = calculate_final_grade(user.userid, user_class.classid)

            all_grades.append({
                "user_id": user.userid,
                "name": user.name,
                "class_name": user_class.name,  # Class name
                "quiz_score": average_quiz_score,  # Separate quiz score
                "assessment_score": assessment_score,  # Separate assessment score
                "final_score": final_score,  # Final score as the average of the two
                "grade": get_grade(final_score),  # Function to calculate grade based on final score
                "class_id": user_class.classid,
                "is_access_granted": is_access_granted  # Get access status from UserClass model
            })

    return render_template('admin_grading.html', all_grades=all_grades)

#Grading scheme
def get_grade(final_score):
    """Determine grade based on final score."""
    if final_score >= 90:
        return 'A'
    elif final_score >= 80:
        return 'B'
    elif final_score >= 70:
        return 'C'
    elif final_score >= 60:
        return 'D'
    else:
        return 'F'
    

# User page to display grades
@grading_bp.route('/my-grades', methods=['GET'])
@login_required
def user_gradebook():
    """Displays the logged-in user's grades, grouped by class."""
    
    # Get the current logged-in user
    user_id = current_user.userid  # Assuming current_user is already set by login_manager

    # Fetch the user's classes
    user_classes = db.session.query(Class).join(UserClass).filter(UserClass.userid == user_id).all()
    user_grades = []

    # Flag to check if grades are available
    grades_available = False

    # Loop through each class to calculate grades
    for user_class in user_classes:
        # Calculate quiz, assessment, and final scores for each class
        average_quiz_score, assessment_score, final_score = calculate_final_grade(user_id, user_class.classid)

        # Check if access to download certificate is granted
        is_access_granted = UserClass.is_access_granted  # Assuming this column exists in UserClass

        # If either score is 0.0, mark the grade as Pending
        if assessment_score == 0.0:
            user_grades.append({
                "class_name": user_class.name,  # Class name
                "quiz_score": average_quiz_score, # Quiz score
                "assessment_score": "Pending",  # Mark as Pending
                "final_score": "Pending",  # Mark final score as Pending
                "grade": "Pending",  # Mark grade as Pending
                "class_id": user_class.classid,
                "is_access_granted": is_access_granted  # Pass certificate access status
            })
        else:
            user_grades.append({
                "class_name": user_class.name,  # Class name
                "quiz_score": average_quiz_score,  # Quiz score
                "assessment_score": assessment_score,  # Assessment score
                "final_score": final_score,  # Final score as the average of the two
                "grade": get_grade(final_score),  # Function to calculate grade based on final score
                "class_id": user_class.classid,
                "is_access_granted": is_access_granted  # Pass certificate access status
            })

    # If no grades are available, add a "No grade available yet" message
    if not user_grades:
        user_grades = [{"message": "No grade available yet"}]

    return render_template('user_grade.html', user_grades=user_grades)

@grading_bp.route('/admin/grant_certificate_access', methods=['POST'])
@login_required
def grant_certificate_access():
    """Allows the admin to grant or revoke certificate access for users."""
    
    # Check if the user has admin privileges
    if not current_user.role:  # Ensure only admins can access
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    user_id = request.form.get('user_id')
    class_id = request.form.get('class_id')

    # Find the UserClass entry
    user_class_entry = UserClass.query.filter_by(userid=user_id, classid=class_id).first()

    if user_class_entry:
        # Toggle the access permission
        user_class_entry.is_access_granted = not user_class_entry.is_access_granted
        db.session.commit()
        flash('Certificate access updated successfully!', 'success')
    else:
        flash('User-Class entry not found!', 'error')

    return redirect(url_for('grading.admin_gradebook'))

# Function to generate a certificate
def generate_certificate(user_name, class_name):
    """Generate a certificate for a user."""
    
    buffer = BytesIO()
    custom_page_size = (letter[0], letter[1] - 200)  # Reduce height by 200 units
    c = canvas.Canvas(buffer, pagesize=custom_page_size)
    width, height = custom_page_size

    logo_path = os.path.abspath("C:/RecyGloLMS/RecyGloLMS/recyglolms/static/img/Recyglo logo.png")

    # Add border
    c.setLineWidth(4)
    c.rect(30, 30, width - 60, height - 60)

    # Add logo if provided
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, width / 2 - 50, height - 150, width=100, height=100, preserveAspectRatio=True, mask='auto')
    else:
        print(f"Logo not found at {logo_path}")
    
    # Certificate title
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 200, "Certificate of Completion")
    
    # Subtitle
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 250, "This is to certify that")
    
    # User name
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 290, user_name)
    
    # Course name
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, height - 330, "Has successfully completed the course:")
    
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 370, class_name)
    
    # Date
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 500, f"Date: {date.today().strftime('%B %d, %Y')}")
    
    # Signature placeholder
    c.line(400, height - 520, 550, height - 520)
    c.setFont("Helvetica", 12)
    c.drawString(420, height - 540, "Authorized Signature")
    
    # Save the PDF
    c.save()
    buffer.seek(0)
    return buffer

# Download certificate route
@grading_bp.route('/download_certificate/<int:class_id>', methods=['GET'])
@login_required
def download_certificate(class_id):
    """Allows users to download their certificate if access is granted."""

    # Find the UserClass entry
    user_class_entry = UserClass.query.filter_by(userid=current_user.userid, classid=class_id).first()

    if not user_class_entry or not user_class_entry.is_access_granted:
        flash('Certificate access is not granted yet.', 'error')
        return redirect(url_for('grading.user_gradebook'))  # Redirect to user's dashboard

    # Fetch class name based on class_id
    user_class = Class.query.filter_by(classid=class_id).first()
    if not user_class:
        flash('Class not found!', 'error')
        return redirect(url_for('grading.user_gradebook'))

    certificate_buffer = generate_certificate(current_user.name, user_class.name)

    return send_file(certificate_buffer, as_attachment=True, download_name="certificate.pdf", mimetype="application/pdf")
