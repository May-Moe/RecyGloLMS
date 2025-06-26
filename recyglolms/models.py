from datetime import datetime
from flask_login import UserMixin
from recyglolms import db
from sqlalchemy.sql import func


# # Initialize db as None at first
# db = None

# # Import db lazily inside the function
# def get_db():
#     from recyglolms.__init__ import db
#     return db

# # db = get_db()
# from flask_sqlalchemy import SQLAlchemy

# # Initialize db here instead of __init__.py
# db = SQLAlchemy()


class User(db.Model, UserMixin):
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    profile_img = db.Column(db.String(200), nullable=True, default="/static/uploads/default-profile.jpg")
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer, default=0)  # 0 = User, 1 = Admin, 2 = Sub-Admin
    last_login = db.Column(db.DateTime, default=None)  # New field for last login time
    level = db.Column(db.String(20), nullable=False, default="Beginner") # New field for user level (default to Beginner)

    # announcements = db.relationship('Announcement', backref='user', lazy=True)
    # progress = db.relationship('Progress', backref='user', lazy=True)  # Tracks user progress on videos
    announcements = db.relationship('Announcement', backref='user', lazy=True, cascade="all, delete")
    progress = db.relationship('Progress', backref='user', lazy=True, cascade="all, delete")
    
    # Relationship with classes
    classes = db.relationship('UserClass', backref='user', lazy=True, cascade="all, delete")
    uploads = db.relationship('Upload', backref='user', lazy=True, cascade="all, delete")
    action_logs = db.relationship('ActionLog', backref='user', lazy=True, cascade="all, delete")
    password_resets = db.relationship('PasswordReset', backref='user', lazy=True, cascade="all, delete")
    activities = db.relationship('Activity', backref='user', lazy=True, cascade="all, delete")

    def get_id(self):
        """Override Flask-Login's get_id method."""
        return str(self.userid)
    
    
    # Method to get users who attempted a specific assessment
    @classmethod
    def get_users_for_assessment(cls, assessment_id):
        return db.session.query(User).join(Assese_Response, User.userid == Assese_Response.user_id)\
                                       .join(Assese_Questions, Assese_Response.question_id == Assese_Questions.id)\
                                       .filter(Assese_Questions.assessment_id == assessment_id)\
                                       .distinct().all()
    
class PasswordReset(db.Model):
    __tablename__ = 'Reset'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)  # Add expiration_time field
    
    # user = db.relationship('User', backref=db.backref('password_resets', lazy=True))
    
    def __init__(self, user_id, otp, created_at, expiration_time):
        self.user_id = user_id
        self.otp = otp
        self.created_at = created_at
        self.expiration_time = expiration_time
    
    
class ActionLog(db.Model):
    __tablename__ = 'ActionLog' # Specify table name explicitly if needed
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    username = db.Column(db.String(100), nullable=False)  # Store the username of the user performing the action
    action_type = db.Column(db.String(50), nullable=False)  # e.g., "create", "update", "delete"
    target_table = db.Column(db.String(50), nullable=False)  # e.g., "user"
    target_id = db.Column(db.Integer, nullable=False)  # ID of the user being affected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.String(255))  # Optionally store detailed info like what fields were updated

    # user = db.relationship('User', backref=db.backref('action_logs', lazy=True))

    def __repr__(self):
        return f"<ActionLog {self.action_type} by {self.username} on {self.timestamp}>"


class Announcement(db.Model):
    announcementid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    announcement_img = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)


class Upload(db.Model):
    uploadid = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)
    uploaddate = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)


class Activity(db.Model):
    activityid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    image = db.relationship('ActivityImage', backref='activity_ref', lazy=True, cascade="all, delete-orphan")
    
    @classmethod
    def count_distinct_activities(cls, user_id):
        """
        Function to count distinct activity IDs across all activities for a given user.
        """
        # Query distinct activity IDs based on user_id and count them
        distinct_activity_count = db.session.query(db.func.count(db.distinct(cls.activityid))) \
                                             .filter(cls.userid == user_id) \
                                             .scalar()
        return distinct_activity_count

class ActivityImage(db.Model):
    __tablename__ = 'activity_image'
    id = db.Column(db.Integer, primary_key=True)
    activityid = db.Column(db.Integer, db.ForeignKey('activity.activityid'), nullable=False)
    activity_image = db.Column(db.String(200), nullable=False)


class Course(db.Model):
    courseid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to modules
    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete")
    
    # Relationship to classes
    classes = db.relationship('CourseClass', backref='course', lazy=True, cascade="all, delete")


    def calculate_course_progress(self, userid):
        """
        Calculate the overall course progress for a user by summing up progress
        from all videos in all modules of this course.
        """
        total_videos = 0
        total_progress = 0

        # Loop through each module in the course
        for module in self.modules:
            # Get the progress for the current module
            module_progress = module.calculate_module_progress(userid)
            
            # Add the number of videos in this module
            total_videos += len(module.videos)
            
            # Add the total progress from this module (each video's progress is weighted)
            total_progress += (module_progress * len(module.videos))

        # Return the overall progress percentage
        return (total_progress / total_videos) if total_videos > 0 else 0


class Module(db.Model):
    moduleid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), nullable=False)
    videos = db.relationship('Video', backref='module', lazy=True, cascade="all, delete")
    quizzes = db.relationship('Quiz', backref='module', lazy=True, cascade="all, delete")
    
    def calculate_module_progress(self, userid):
        """
        Calculate the overall module progress for a user by summing up progress
        for all videos in this module.
        """
        videos = self.videos
        total_videos = len(videos)
        completed_videos = 0

        # Loop through each video in the module
        for video in videos:
            progress = Progress.query.filter_by(userid=userid, videoid=video.videoid).first()
            
            # If the video is completed, add to the count
            if progress and progress.completed:
                completed_videos += 1

        # Calculate the percentage of videos completed in this module
        return (completed_videos / total_videos) * 100 if total_videos > 0 else 0


class Video(db.Model):
    videoid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    moduleid = db.Column(db.Integer, db.ForeignKey('module.moduleid'), nullable=False)


class Progress(db.Model):
    progressid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    videoid = db.Column(db.Integer, db.ForeignKey('video.videoid'), nullable=False)
    watched_duration = db.Column(db.Integer, default=0)  # Duration watched in seconds
    completed = db.Column(db.Boolean, default=False)

    def calculate_video_progress(self):
        video = Video.query.get(self.videoid)
        if video and video.duration > 0:
            progress_percentage = (self.watched_duration / video.duration) * 100
            return min(progress_percentage, 100)
        return 0

    def update_progress(self, watched_duration, completed):
        self.watched_duration = watched_duration
        self.completed = completed
        db.session.commit()
        
# New models for Quizzes

class Quiz(db.Model):
    quizid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)  # Quiz title
    description = db.Column(db.Text, nullable=True)  # Optional description
    moduleid = db.Column(db.Integer, db.ForeignKey('module.moduleid'), nullable=False)  # Foreign key to Module
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='quiz', lazy=True,)  # Relationship with questions
    time_limit = db.Column(db.Integer, nullable=True, default=5)  # Default 5 minutes
    
    # Define the relationship with UserResponse
    # user_responses = db.relationship('UserResponse', backref='quiz', lazy=True)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    user_responses = db.relationship('UserResponse', backref='quiz', lazy=True, cascade="all, delete")


class Question(db.Model):
    questionid = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)  # The question text
    quizid = db.Column(db.Integer, db.ForeignKey('quiz.quizid'), nullable=False)  # Foreign key to Quiz
    answers = db.relationship('Answer', backref='question', lazy=True, cascade="all, delete-orphan")  # Relationship with answers


class Answer(db.Model):
    answerid = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)  # Answer text
    is_correct = db.Column(db.Boolean, default=False)  # Whether this is the correct answer
    questionid = db.Column(db.Integer, db.ForeignKey('question.questionid'), nullable=False)  # Foreign key to Question


class UserResponse(db.Model):
    __tablename__ = 'userresponse'  # Specify table name explicitly if needed
    responseid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)  # Foreign key to User
    quizid = db.Column(db.Integer, db.ForeignKey('quiz.quizid'), nullable=False)  # Foreign key to Quiz
    score = db.Column(db.Float, default=0)  # Total score for the quiz
    created_date = db.Column(db.DateTime, default=datetime.utcnow)  # When the user took the quiz
    user_answers = db.relationship('UserAnswer', backref='response', lazy=True, cascade="all, delete-orphan")  # Relationship with UserAnswers


class UserAnswer(db.Model):
    __tablename__ = 'useranswer'  # Specify table name explicitly if needed
    useranswerid = db.Column(db.Integer, primary_key=True)
    responseid = db.Column(db.Integer, db.ForeignKey('userresponse.responseid'), nullable=False)  # Foreign key to UserResponse
    questionid = db.Column(db.Integer, db.ForeignKey('question.questionid'), nullable=False)  # Foreign key to Question
    answerid = db.Column(db.Integer, db.ForeignKey('answer.answerid'), nullable=False)  # Foreign key to Answer
    is_correct = db.Column(db.Boolean, default=False)  # Whether the selected answer was correct
    
      # Relationships
    question = db.relationship('Question', backref='user_answers', lazy=True)
    answer = db.relationship('Answer', backref='user_answers', lazy=True)
    
    
# New models for Feedbacks
class Feedback(db.Model):
    __tablename__ = 'feedback' # Specify table name explicitly if needed
    feedbackid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    feedback = db.Column(db.Text, nullable=False)  # Feedback text
    submit_date = db.Column(db.DateTime, default=datetime.utcnow)  # Submission timestamp

    user = db.relationship('User', backref='feedbacks')
    
    
# New models for Classes
class Class(db.Model):
    __tablename__ = 'class'  # Explicitly set the table name
    classid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to link courses
    courses = db.relationship('CourseClass', backref='class_', lazy=True)
    users = db.relationship('UserClass', backref='class_', lazy=True)


class CourseClass(db.Model):
    """Link table between courses and classes"""
    __tablename__ = 'CourseClass'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    classid = db.Column(db.Integer, db.ForeignKey('class.classid'), nullable=False)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), nullable=False)


class UserClass(db.Model):
    """Link table between users and classes"""
    __tablename__ = 'UserClass'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    classid = db.Column(db.Integer, db.ForeignKey('class.classid'), nullable=False)
    is_access_granted = db.Column(db.Boolean, default=False)  # To track if the admin granted access to the class for certificate generation
    
#Notification feature
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    
    
#Assessment feature    
class Assessment(db.Model):
    __tablename__ = 'assessment'  # Ensure correct casing
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, nullable=False)  # Ensure it stores user ID
    time_limit = db.Column(db.Integer, nullable=False)
    classid = db.Column(db.Integer, db.ForeignKey('class.classid'), nullable=False)
    
    # Method to get all assessments for a specific class
    @classmethod
    def get_assessments_for_class(cls, classid):
        return db.session.query(cls).filter_by(classid=classid).all()

class Assese_Questions(db.Model):
    __tablename__ = 'assess_questions'
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False) 
    question = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

class Assese_Response(db.Model):
    __tablename__ = 'assess_response'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('assess_questions.id'), nullable=False)  # Fixed reference
    user_id = db.Column(db.Integer, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Float, nullable=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)  # Add this line
    plagiarism_score = db.Column(db.Float, nullable=True)  # Store plagiarism percentage

    # Relationships
    assessment = db.relationship('Assessment', backref=db.backref('responses', lazy=True))
    assess_question = db.relationship('Assese_Questions', backref='responses') 

    # Method to get responses for a specific user and assessment
    @classmethod
    def get_users_for_assessment(cls, assessment_id):
        return db.session.query(
            User.userid, 
            User.name, 
            db.func.coalesce(db.func.sum(Assese_Response.marks), 0).label("marks")
        ).join(Assese_Response, User.userid == Assese_Response.user_id)\
        .join(Assese_Questions, Assese_Response.question_id == Assese_Questions.id)\
        .filter(Assese_Questions.assessment_id == assessment_id)\
        .group_by(User.userid, User.name)\
        .all()
        
    # Method to calculate total marks for a specific user and assessment
    @classmethod
    def calculate_total_marks(cls, user_id, assessment_id):
        total_marks = db.session.query(db.func.coalesce(db.func.sum(Assese_Response.marks), 0))\
                                .join(Assese_Questions, Assese_Response.question_id == Assese_Questions.id)\
                                .filter(Assese_Questions.assessment_id == assessment_id, Assese_Response.user_id == user_id)\
                                .scalar()
        return total_marks
    @classmethod
    def get_latest_responses_by_user_and_assessment(cls, user_id, assessment_id):
        subquery = db.session.query(
            cls.question_id, 
            db.func.max(cls.id).label('latest_id')
        ).filter(cls.user_id == user_id, cls.assessment_id == assessment_id).group_by(cls.question_id).subquery()

        query = db.session.query(cls, Assese_Questions)\
                        .join(subquery, cls.id == subquery.c.latest_id)\
                        .join(Assese_Questions, cls.question_id == Assese_Questions.id)

        print(str(query))  # Debugging line to check generated SQL query
        return query.all()
    
class Event(db.Model):
    __tablename__ = 'events'  # Explicitly name the table 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True) # To store a link to an event image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New columns
    speaker_names = db.Column(db.JSON, nullable=True)  # store list of names in JSON format like ['John', 'Alice']
    category = db.Column(db.String(100), nullable=True)
    youtube_link = db.Column(db.String(255), nullable=True)
        
    # Optional: Link to the user who created the event
    user_id = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    user = db.relationship('User', backref=db.backref('events', lazy=True))

    def __repr__(self):
        return f"<Event {self.title}>"

# class Certificate(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
#     course_name = db.Column(db.String(255), nullable=False)
#     issue_date = db.Column(db.Date, nullable=False)
#     file_path = db.Column(db.String(255), nullable=False)  # Path to certificate file

#     user = db.relationship('User', backref=db.backref('certificates', lazy=True))