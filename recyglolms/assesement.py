from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from recyglolms.__inti__ import db
from recyglolms.models import Assese_Response, Assessment, Assese_Questions, User, Class
import os
import json
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

# User: Submit Answers (Plagiarism Check)
@assessment_bp.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.form
    question_id = data.get("question_id")
    answer_text = data.get("answer_text")

    if not question_id or not answer_text:
        return jsonify({"success": False, "error": "Missing required fields"})

    existing_answers = [ans.answer_text for ans in Assese_Response.query.all()]
    
    for past_answer in existing_answers:
        similarity_score = textdistance.jaccard.normalized_similarity(answer_text, past_answer)
        if similarity_score > 0.7:
            return jsonify({"success": False, "error": "Plagiarism detected!"})

    new_response = Assese_Response(
        question_id=question_id, 
        user_id=current_user.id, 
        answer_text=answer_text
    )
    db.session.add(new_response)
    db.session.commit()

    return jsonify({"success": True, "message": "Answer submitted successfully"})