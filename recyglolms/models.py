from recyglolms.__inti__ import db  # Import db from __init__.py
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    profile_img = db.Column(db.String(200), nullable=True, default="/static/uploads/default-profile.jpg")
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer, default=0)  # 0 = User, 1 = Admin, 2 = Sub-Admin
    last_login = db.Column(db.DateTime, default=None)  # New field for last login time
    level = db.Column(db.String(20), nullable=False, default="Beginner") # New field for user level (default to Beginner)

    announcements = db.relationship('Announcement', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)  # Tracks user progress on videos
    
    # Relationship with classes
    classes = db.relationship('UserClass', backref='user', lazy=True)

    def get_id(self):
        """Override Flask-Login's get_id method."""
        return str(self.userid)
    
    
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

    user = db.relationship('User', backref=db.backref('action_logs', lazy=True))

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
    modules = db.relationship('Module', backref='course', lazy=True)
    
       # Relationship to classes
    classes = db.relationship('CourseClass', backref='course', lazy=True)

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
    videos = db.relationship('Video', backref='module', lazy=True)
    quizzes = db.relationship('Quiz', backref='module', lazy=True)  # Add this line
    
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
    
    # Define the relationship with UserResponse
    user_responses = db.relationship('UserResponse', backref='quiz', lazy=True)


class Question(db.Model):
    questionid = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)  # The question text
    quizid = db.Column(db.Integer, db.ForeignKey('quiz.quizid'), nullable=False)  # Foreign key to Quiz
    answers = db.relationship('Answer', backref='question', lazy=True)  # Relationship with answers


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
    user_answers = db.relationship('UserAnswer', backref='response', lazy=True)  # Relationship with UserAnswers


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