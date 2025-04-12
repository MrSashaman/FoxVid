from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    videos = db.relationship('Video', backref='author', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=False)
    views = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class VideoView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
