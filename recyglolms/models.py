from recyglolms.__inti__ import db  # Import db from __init__.py
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Boolean, default=False)  # False for regular user, True for admin

    announcements = db.relationship('Announcement', backref='user', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)  # Tracks user progress on videos

    # Override Flask-Login's get_id method
    def get_id(self):
        return str(self.userid)


class Announcement(db.Model):
    announcementid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    announcement_img = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)


# Upload table
class Upload(db.Model):
    uploadid = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)
    uploaddate = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)


# Activity table
class Activity(db.Model):
    activityid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)


# Course table
class Course(db.Model):
    courseid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    modules = db.relationship('Module', backref='course', lazy=True)  # One-to-many relationship with modules

    def calculate_course_progress(self, userid):
        """
        Calculate overall course progress for a user by summing up progress
        from all videos in all modules of this course.
        """
        total_videos = 0
        total_progress = 0

        for module in self.modules:
            for video in module.videos:
                total_videos += 1
                progress = Progress.query.filter_by(userid=userid, videoid=video.videoid).first()
                if progress:
                    total_progress += progress.calculate_video_progress()

        return total_progress / total_videos if total_videos > 0 else 0


# Module table
class Module(db.Model):
    moduleid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    courseid = db.Column(db.Integer, db.ForeignKey('course.courseid'), nullable=False)
    videos = db.relationship('Video', backref='module', lazy=True)  # One-to-many relationship with videos


# Video table
class Video(db.Model):
    videoid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)  # Video URL or path
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    moduleid = db.Column(db.Integer, db.ForeignKey('module.moduleid'), nullable=False)


# Progress table
class Progress(db.Model):
    progressid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    videoid = db.Column(db.Integer, db.ForeignKey('video.videoid'), nullable=False)
    watched_duration = db.Column(db.Integer, default=0)  # Duration watched in seconds
    completed = db.Column(db.Boolean, default=False)  # Whether the video is fully watched

    def calculate_video_progress(self):
        """
        Calculate the percentage of a video that has been watched.
        """
        video = Video.query.get(self.videoid)
        if video and video.duration > 0:
            return (self.watched_duration / video.duration) * 100
        return 0