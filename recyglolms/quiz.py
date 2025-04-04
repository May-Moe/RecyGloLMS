from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from recyglolms import db  # Fixed import
from recyglolms.models import Quiz, Question, Answer, Module, Course, UserResponse, UserAnswer, Class
import json  # Use built-in json module

quiz_bp = Blueprint('quiz', __name__)

#admin-side funtionalities

# View all quizzes (Admin only)
@quiz_bp.route('/quizzes', methods=['GET'])
@login_required
def view_all_quizzes():
    if not current_user.role:  # Ensure correct role validation
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    courses = Course.query.all()  # Fetch all courses

    # Create a dictionary to store modules and their quizzes per course
    course_module_data = {}
    for course in courses:
        modules = Module.query.filter_by(courseid=course.courseid).all()
        course_module_data[course.courseid] = []

        for module in modules:
            quizzes = Quiz.query.filter_by(moduleid=module.moduleid).all()
            course_module_data[course.courseid].append({
                "module": module,
                "quizzes": quizzes  # Attach quizzes to the correct module
            })

    return render_template('viewall_quizzes.html', 
                           courses=courses, 
                           course_module_data=course_module_data,  # Pass module & quiz data
                           current_user_name=current_user.name,
                           current_user_email=current_user.email,
                        current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template


# Create Quiz
@quiz_bp.route('/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if not current_user.role:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        quiz_title = request.form.get('quiz_title')
        quiz_description = request.form.get('quiz_description')
        module_id = request.form.get('module_id')
        questions_data = request.form.get('questions_data')  # JSON from frontend
        time_limit = request.form.get('time_limit')  # Get time limit from the form

        if not (quiz_title and module_id and questions_data and time_limit):
            flash("All fields including time limit are required!", "danger")
            return redirect(url_for('quiz.create_quiz'))

        try:
            time_limit = int(time_limit)  # Ensure it's an integer
        except ValueError:
            flash("Invalid time limit!", "danger")
            return redirect(url_for('quiz.create_quiz'))

        new_quiz = Quiz(title=quiz_title, description=quiz_description, moduleid=module_id, time_limit=time_limit)
        db.session.add(new_quiz)
        db.session.flush()

        try:
            questions_list = json.loads(questions_data)
        except json.JSONDecodeError:
            flash("Invalid question data!", "danger")
            return redirect(url_for('quiz.create_quiz'))

        for question in questions_list:
            question_text = question.get('question', '').strip()
            answers = question.get('answers', [])
            correct_answer_index = int(question.get('correct_answer', -1))

            if not question_text or len(answers) != 4:
                continue

            new_question = Question(text=question_text, quizid=new_quiz.quizid)
            db.session.add(new_question)
            db.session.flush()

            for index, answer_text in enumerate(answers):
                is_correct = index == correct_answer_index
                new_answer = Answer(text=answer_text, is_correct=is_correct, questionid=new_question.questionid)
                db.session.add(new_answer)

        db.session.commit()
        flash("Quiz created successfully with a time limit!", "success")
        return redirect(url_for('quiz.view_all_quizzes'))

    module_id = request.args.get('module_id')
    if not module_id:
        flash("Module ID is required!", "danger")
        return redirect(url_for('quiz.view_all_quizzes'))

    module = Module.query.get(module_id)
    if not module:
        flash("Module not found!", "danger")
        return redirect(url_for('quiz.view_all_quizzes'))

    course = Course.query.get(module.courseid)
    if not course:
        flash("Course not found!", "danger")
        return redirect(url_for('quiz.view_all_quizzes'))

    return render_template('create_quiz.html', module=module, course=course,
                           current_user_name=current_user.name,
                           current_user_email=current_user.email,
                           current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)


# View Quiz
@quiz_bp.route('/view_quiz/<int:quiz_id>', methods=['GET'])
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for('quiz.view_all_quizzes'))

    questions = Question.query.filter_by(quizid=quiz_id).all()
    quiz_data = []
    for question in questions:
        answers = Answer.query.filter_by(questionid=question.questionid).all()
        quiz_data.append({'question': question, 'answers': answers})

    return render_template('view_quiz.html', quiz=quiz, quiz_data=quiz_data,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template



@quiz_bp.route('/update_question', methods=['POST'])
def update_question():
    data = request.json  # Parse JSON data from frontend
    question_id = data.get("question_id")
    question_text = data.get("text")
    answers = data.get("answers", [])

    question = Question.query.get(question_id)
    if not question:
        return jsonify({"message": "Question not found"}), 404

    # Update question text
    question.text = question_text

    # Collect answer IDs that should be marked correct
    correct_answer_ids = {answer_data.get("answer_id") for answer_data in answers if answer_data.get("is_correct")}

    # Update answers
    for answer_data in answers:
        answer_id = answer_data.get("answer_id")
        answer_text = answer_data.get("text")

        answer = Answer.query.get(answer_id)
        if answer:
            answer.text = answer_text
            answer.is_correct = answer_id in correct_answer_ids  # Set correct answer

    db.session.commit()

    return jsonify({"message": "Question updated successfully"}), 200


# Delete Quiz
@quiz_bp.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    if not current_user.role:
        return jsonify({"error": "Unauthorized access!"}), 403

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Delete all related questions and answers
    questions = Question.query.filter_by(quizid=quiz_id).all()
    for question in questions:
        Answer.query.filter_by(questionid=question.questionid).delete()
        db.session.delete(question)
    
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('quiz.view_all_quizzes'))

# User side quiz functionalities

@quiz_bp.route('/quizzes')
@login_required
def user_quizzes():
    """Display all available quizzes."""
    quizzes = Quiz.query.all()
    return render_template('user_quizzes.html', quizzes=quizzes,
                                                   current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template


@quiz_bp.route('/quiz/<int:quizid>', methods=['GET', 'POST'])
@login_required
def start_quiz(quizid):
    """Start a quiz and display questions."""
    quiz = Quiz.query.get_or_404(quizid)
    return render_template('start_quiz.html', quiz=quiz,
                           current_user_name = current_user.name,
                            current_user_email = current_user.email,
                            current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template


@quiz_bp.route('/quiz/<int:quizid>/submit', methods=['POST'])
@login_required
def submit_quiz(quizid):
    """Handles quiz submission and calculates the score."""
    quiz = Quiz.query.get_or_404(quizid)
    
    # Create a new UserResponse entry for the quiz attempt
    user_response = UserResponse(userid=current_user.userid, quizid=quizid, score=0)
    db.session.add(user_response)
    db.session.commit()  # Commit to get responseid

    score = 0
    total_questions = len(quiz.questions)

    for question in quiz.questions:
        answer_id = request.form.get(f'question_{question.questionid}')
        if answer_id:
            selected_answer = Answer.query.get(int(answer_id))
            is_correct = selected_answer.is_correct

            # Store the user's answer
            user_answer = UserAnswer(
                responseid=user_response.responseid,
                questionid=question.questionid,
                answerid=selected_answer.answerid,
                is_correct=is_correct
            )
            db.session.add(user_answer)

            if is_correct:
                score += 1

    # Update final score
    user_response.score = (score / total_questions) * 100  # Convert to percentage
    db.session.commit()

    return redirect(url_for('quiz.quiz_result', responseid=user_response.responseid))

@quiz_bp.route('/quiz/result/<int:responseid>')
@login_required
def quiz_result(responseid):
    """Display the quiz results and user answers for all attempts."""
    # Get the current user's response for the specific attempt
    user_response = UserResponse.query.get_or_404(responseid)

    # Ensure user is only viewing their own results
    if user_response.userid != current_user.userid:
        return "Unauthorized", 403

    # Get the quiz object using the quizid from the user_response
    quiz = Quiz.query.get_or_404(user_response.quizid)

    # Get the module associated with this quiz
    module = Module.query.get_or_404(quiz.moduleid)

    # Get all attempts (user quiz results) for this quiz and order by responseid descending (latest first)
    user_quiz_results = UserResponse.query.filter_by(userid=current_user.userid, quizid=user_response.quizid) \
                                           .order_by(UserResponse.responseid.desc()).all()

    # Get the user's answers for the current attempt
    user_answers = UserAnswer.query.filter_by(responseid=responseid).all()

    # Get answers for each previous attempt as well
    for result in user_quiz_results:
        result.answers = UserAnswer.query.filter_by(responseid=result.responseid).all()

    # Render the quiz result page with all user quiz results and answers
    return render_template('quiz_result.html',
                           user_response=user_response, 
                           user_answers=user_answers, 
                           score=user_response.score,
                           user_quiz_results=user_quiz_results,
                           quiz=quiz,  # Pass the quiz object to the template
                           module=module,  # Pass the module object to the template
                           current_user_name=current_user.name,
                           current_user_email=current_user.email,
                                                   current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template


@quiz_bp.route('/quiz/summary/<int:quiz_id>')
@login_required
def summary_mark(quiz_id):
    """Display a summary of the user's quiz attempts for a specific quiz."""
    
    # Fetch only the attempts for the current quiz
    user_quiz_results = UserResponse.query.filter_by(userid=current_user.userid, quizid=quiz_id) \
                                          .order_by(UserResponse.responseid.desc()).all()

    # Fetch the quiz object for this quiz_id
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch the associated module object (if necessary)
    module = Module.query.get_or_404(quiz.moduleid)

    if not user_quiz_results:
        return render_template('summary_mark.html', user_quiz_results=[], 
                               current_user_name=current_user.name, 
                               current_user_email=current_user.email,
                               quiz=quiz,  # Pass the quiz object to the template
                               module=module,
                                       current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template

    return render_template('summary_mark.html', user_quiz_results=user_quiz_results, 
                           current_user_name=current_user.name, 
                           current_user_email=current_user.email,
                           quiz=quiz,  # Pass the quiz object to the template
                           module=module,
                        current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template
  # Pass the module object to the template

# View all quizzes (Admin only)
@quiz_bp.route('/manage_assessment', methods=['GET'])
@login_required
def view_all_assessment():
    if not current_user.role:  # Ensure correct role validation
        flash("Unauthorized access!", "danger")
        return redirect(url_for('auth.login'))

    courses = Course.query.all()  # Fetch all courses
    classes = Class.query.all()
    return render_template('manage_assessment.html', 
                           courses=courses, 
                           classes=classes,
                           current_user_name=current_user.name,
                           current_user_email=current_user.email,
                        current_user_image=url_for('static', filename=current_user.profile_img) if current_user.profile_img else None)  # Pass the module object to the template
