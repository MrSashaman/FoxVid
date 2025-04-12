import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Video, VideoView

from database import db
from models import Video
from extensions import db  # Теперь импорт идёт из extensions.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['THUMBNAIL_FOLDER'] = os.path.join(os.getcwd(), 'thumbnails')
app.config['SECRET_KEY'] = '997265'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

db.init_app(app)  # Важно!


with app.app_context():
    db.create_all()

@app.route('/watch/<int:video_id>')
@login_required
def watch_video(video_id):
    video = Video.query.get_or_404(video_id)

    # Проверяем, смотрел ли пользователь это видео
    existing_view = VideoView.query.filter_by(user_id=current_user.id, video_id=video.id).first()
    if not existing_view:
        video.views += 1
        db.session.add(VideoView(user_id=current_user.id, video_id=video.id))
        db.session.commit()

    return render_template('watch.html', video=video)

def save_thumbnail(image, filename):
    image = Image.open(image)
    image = image.resize((320, 180))  # Уменьшаем размер для отображения на главной
    thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename)
    image.convert("RGB").save(thumbnail_path, "JPEG")
    return filename

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_video():
    if request.method == 'POST':
        if 'video' not in request.files or 'thumbnail' not in request.files:
            return redirect(request.url)

        video_file = request.files['video']
        thumbnail_file = request.files['thumbnail']
        title = request.form.get('title', 'Без названия')
        category = request.form.get('category', 'Другое')

        if video_file.filename == '' or thumbnail_file.filename == '':
            return redirect(request.url)

        video_filename = video_file.filename
        thumbnail_filename = f"thumb_{video_filename}.jpg"

        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video_file.save(video_path)
        # save_thumbnail(thumbnail_file, thumbnail_filename) # Предполагается, что это ваша функция

        new_video = Video(
            filename=video_filename,
            title=title,
            category=category,
            thumbnail=thumbnail_filename,
            author_id=current_user.id  # **ДОБАВЛЯЕМ AUTHOR_ID**
        )
        db.session.add(new_video)
        db.session.commit()

        return redirect(url_for('index'))

    categories = ['Наука', 'Игры', 'Фильмы', 'Музыка', 'Спорт', 'Другое', 'Разработка']
    return render_template('add.html', categories=categories)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Такой пользователь уже существует!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Теперь войдите в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    videos = Video.query.all()
    return render_template('index.html', videos=videos)

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def serve_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
