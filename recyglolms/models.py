from recyglolms.__inti__ import db  # Import db from __init__.py
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Boolean, default=False)  # False for regular user, True for admin
    last_login = db.Column(db.DateTime, default=None)  # New field for last login time

    announcements = db.relationship('Announcement', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)  # Tracks user progress on videos

    def get_id(self):
        """Override Flask-Login's get_id method."""
        return str(self.userid)


class Announcement(db.Model):
    announcementid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    announcement_img = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
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


class Course(db.Model):
    courseid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    modules = db.relationship('Module', backref='course', lazy=True)

    def calculate_course_progress(self, userid):
        """
        Calculate the overall course progress for a user by summing up progress
        from all videos in all modules of this course.
        """
        total_videos = 0
        total_progress = 0

        for module in self.modules:
            module_progress = module.calculate_module_progress(userid)
            total_videos += len(module.videos)
            total_progress += module_progress * len(module.videos)

        return (total_progress / total_videos) if total_videos > 0 else 0


class Module(db.Model):
    moduleid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), nullable=False)
    videos = db.relationship('Video', backref='module', lazy=True)
    
    def calculate_module_progress(self, userid):
        """
        Calculate the overall module progress for a user by summing up progress
        for all videos in this module.
        """
        videos = self.videos
        total_videos = len(videos)
        completed_videos = 0

        for video in videos:
            progress = Progress.query.filter_by(userid=userid, videoid=video.videoid).first()
            if progress and progress.completed:
                completed_videos += 1

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