from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from recyglolms.__inti__ import db
from recyglolms.models import Assese_Response, Assessment, Assese_Questions, User, Class, ActionLog
import os
import json
from datetime import datetime, timedelta
import textdistance
from werkzeug.utils import secure_filename

assessment_bp = Blueprint('assessment', __name__)
UPLOAD_FOLDER = "static/uploads"

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@assessment_bp.route('/admin/assessments', methods=['GET'])
@login_required
def view_classes():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    classes = Class.query.all()  # Assuming you have a Class model
    return render_template('admin_assessments.html', classes=classes)

@assessment_bp.route('/admin/assessments/<int:classid>', methods=['GET'])
@login_required
def view_assessments(classid):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    selected_class = Class.query.get_or_404(classid)
    assessments = Assessment.query.filter_by(classid=classid).all()
    
    return render_template('viewall_assessment.html', assessments=assessments, selected_class=selected_class)

@assessment_bp.route('/admin/assessments/<int:classid>/create', methods=['GET', 'POST'])
@login_required
def create_assessment(classid):  #  Change parameter to classid
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    selected_class = Class.query.get_or_404(classid)

    if request.method == 'POST':
        title = request.form.get('title')
        time_limit = request.form.get('time_limit')
        questions_data = request.form.get('questions_data')

        if not (title and time_limit and questions_data):
            flash("All fields are required!", "danger")
            return redirect(url_for('assessment.create_assessment', classid=classid))  #  Use classid

        try:
            time_limit = int(time_limit)
        except ValueError:
            flash("Invalid time limit!", "danger")
            return redirect(url_for('assessment.create_assessment', classid=classid))  # Use classid

        new_assessment = Assessment(
            title=title, 
            created_by=current_user.userid, 
            time_limit=time_limit, 
            classid=classid  #  Use classid instead of class_id
        )
        db.session.add(new_assessment)
        db.session.flush()  

        try:
            questions_list = json.loads(questions_data)
        except json.JSONDecodeError:
            flash("Invalid question data!", "danger")
            return redirect(url_for('assessment.create_assessment', classid=classid))  #  Use classid

        for question in questions_list:
            question_text = question.get('question', '').strip()
            plagiarism_check = question.get('plagiarism_check', False)
            word_limit = question.get('word_limit', None)

            if not question_text:
                continue  

            image_url = None
            if "question_image" in request.files:
                file = request.files["question_image"]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    image_url = file_path

            new_question = Assese_Questions(
                assessment_id=new_assessment.id,  
                question=question_text,
                image_url=image_url
            )
            db.session.add(new_question)

        db.session.commit()
        flash("Assessment created successfully!", "success")
        return redirect(url_for('assessment.view_assessments', classid=classid))  # Use classid

    return render_template('create_assessment.html', selected_class=selected_class)

@assessment_bp.route('/admin/assessment/<int:assessment_id>/answers')
@login_required
def view_attempted_users(assessment_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    # Fetch users who attempted the assessment along with their marks
    users = db.session.query(
        User.userid, 
        User.name, 
        db.func.least(db.func.coalesce(db.func.sum(Assese_Response.marks), 0), 100).label("total_marks")  # Limit to 100
    ).join(Assese_Response, User.userid == Assese_Response.user_id)\
    .join(Assese_Questions, Assese_Response.question_id == Assese_Questions.id)\
    .filter(Assese_Questions.assessment_id == assessment_id)\
    .group_by(User.userid, User.name)\
    .all()

    return render_template('assess_attempt_user.html', users=users, assessment_id=assessment_id)

<<<<<<< HEAD
    new_response = Assese_Response(
        question_id=question_id, 
        user_id=current_user.userid, 
        answer_text=answer_text
    )
    db.session.add(new_response)
    db.session.commit()

    return jsonify({"success": True, "message": "Answer submitted successfully"})


@assessment_bp.route('/delete_assessment/<int:assessment_id>', methods=['POST'])
@login_required
def delete_assessment(assessment_id):
    # Ensure only admins can access
    if not current_user.role:  # Assuming role=1 is admin
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    assessment = Assessment.query.get_or_404(assessment_id)

    # Delete the assessment
    db.session.delete(assessment)
    db.session.commit()

    # Log the deletion
    log_entry = ActionLog(
        userid=current_user.userid,
        username=current_user.name,
        action_type="Delete",
        target_table="assessment",
        target_id=assessment_id,
        timestamp=datetime.now(),
        details=f"Deleted assessment: {assessment.title}"
    )
    db.session.add(log_entry)
    db.session.commit()

    flash("Assessment deleted successfully!", "success")
    return redirect(url_for('assessment.view_classes'))  # Redirect to the assessment view
=======

@assessment_bp.route('/admin/assessment/<int:assessment_id>/answers/<int:user_id>')
@login_required
def view_user_answers(assessment_id, user_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    # Get only the latest responses for each question
    responses = Assese_Response.get_latest_responses_by_user_and_assessment(user_id, assessment_id)

    # Calculate total marks **from stored values**
    total_marks = sum(response.marks or 0 for response, _ in responses)

    return render_template('grade_assessment.html', responses=responses, assessment_id=assessment_id, user_id=user_id, total_marks=total_marks)


@assessment_bp.route('/admin/assessment/<int:assessment_id>/answers/<int:user_id>/grade', methods=['POST'])
@login_required
def grade_user_answers(assessment_id, user_id):
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    total_marks = 0
    responses_to_update = []

    for field_name, marks in request.form.items():
        if field_name.startswith("marks_"):  # Identify valid mark fields
            response_id = int(field_name.split("_")[1])  # Extract response ID
            response = Assese_Response.query.get(response_id)

            if response:
                marks = max(0, min(float(marks), 100))  # Ensure marks are between 0 and 10
                responses_to_update.append((response, marks))
                total_marks += marks

    total_marks = min(total_marks, 100)  # Ensure total does not exceed 100

    # Save marks to database
    for response, marks in responses_to_update:
        response.marks = marks
    db.session.commit()

    flash("Marks assigned successfully!", "success")
    return redirect(url_for('assessment.view_attempted_users', assessment_id=assessment_id))



@assessment_bp.route('/submit_answer/<int:assessment_id>/<int:question_index>', methods=['GET', 'POST'])
@login_required
def submit_answer(assessment_id, question_index):
    assessment = Assessment.query.get(assessment_id)
    if not assessment:
        flash("Assessment not found!", "danger")
        return redirect(url_for('main.learning'))

    # **Check if the user has already completed this assessment**
    existing_responses = Assese_Response.query.filter_by(
        user_id=current_user.userid, assessment_id=assessment_id
    ).first()

    if existing_responses:  # If any response exists, user has already attempted this assessment
        flash("You have already completed this assessment. Redirecting to your answers.", "info")
        return redirect(url_for('assessment.review_answers', assessment_id=assessment_id))
    

    # Fetch questions
    questions = Assese_Questions.query.filter_by(assessment_id=assessment_id).all()
    if question_index >= len(questions):  
        return redirect(url_for('assessment.review_answers', assessment_id=assessment_id))

    current_question = questions[question_index]

    if request.method == 'POST':
        answer_text = request.form.get("answer_text")

        if not answer_text:
            flash("Answer is required!", "danger")
            return redirect(url_for('assessment.submit_answer', assessment_id=assessment_id, question_index=question_index))

        # Save the response
        new_response = Assese_Response(
            question_id=current_question.id, 
            user_id=current_user.userid, 
            answer_text=answer_text,
            assessment_id=assessment_id,
            marks=None
        )
        db.session.add(new_response)
        db.session.commit()

        flash("Answer saved!", "success")

        return redirect(url_for('assessment.submit_answer', assessment_id=assessment_id, question_index=question_index + 1))


    return render_template('user_assess_answer.html', assessment_id=assessment_id, question=current_question,
                           question_index=question_index, total_questions=len(questions), assessment=assessment,
                           existing_responses=existing_responses)


@assessment_bp.route('/review_answers/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
def review_answers(assessment_id):
    responses = Assese_Response.query.filter_by(user_id=current_user.userid, assessment_id=assessment_id).all()
    
    # Fetch the corresponding questions
    assess_questions = {q.id: q for q in Assese_Questions.query.filter_by(assessment_id=assessment_id).all()}
    
    if request.method == 'POST':
        flash("Assessment submitted successfully!", "success")
        return redirect(url_for('main.learning'))

    return render_template('review_answers.html', responses=responses, assessment_id=assessment_id, assess_questions=assess_questions)

>>>>>>> 874eed0c7c68993332b7e8770bac01b1941794c0
