from flask import Flask, render_template, redirect, url_for, flash, request
import smtplib
import os
from sqlalchemy import and_
from forms import RegisterForm, LoginForm, ToDoForm
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from flask_ckeditor import CKEditor
from datetime import datetime
import bleach  # used to make CKEditor more safe

"""
TODO: clicking task should mark them done and clicking done task should mark them undone
TODO: setting for sorting and maybe selecting colors?
TODO: deleting by user tasks from database
"""

load_dotenv()


class Base(DeclarativeBase):
    pass


# configuring app then implementing login manager and database
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')

ckeditor = CKEditor(app)

db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# below are routes that user can take
@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect(url_for('login'))


@app.route('/settings/')
def settings():
    return 'To be implemented'


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = ToDoForm()
    if form.validate_on_submit():
        task = Tasks(importance=form.importance.data, 
                name=form.task.data, description=form.task_description.data,
                    owner=current_user.get_id(), due=form.due.data, time=str(datetime.now()).split('.')[0], done=0)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_task.html', form=form, logged=current_user.is_authenticated)


@app.route('/')
def index():
    tasks = None
    done = None
    if request.args.get('done') == 'True':
        tasks = db.session.execute(db.select(Tasks).where(and_(Tasks.owner == current_user.get_id(), Tasks.done == 1))).scalars().all()
        done = True
    elif current_user.is_authenticated:
        tasks = db.session.execute(db.select(Tasks).where(and_(Tasks.owner == current_user.get_id() and Tasks.done == 0))).scalars().all()
    return render_template('index.html', home=True, logged=current_user.is_authenticated, user=current_user, tasks=tasks, done=done)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        if db.session.execute(db.select(User).where(User.email == form.email.data)).scalar():
            flash("User already exists")
            return render_template('register.html', form=form)
        if db.session.execute(db.select(User).where(User.username == form.nick.data)).scalar():
            flash("Nick already taken")
            return render_template('register.html', form=form)
        hashed_password = generate_password_hash(form.password.data, salt_length=8)
        user = User(username=form.nick.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', form=form, register=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # blocks logged users from logging again
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar()
        try:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
            else:
                flash('Wrong password or email')
        except AttributeError:
            flash('Wrong password or email')

    return render_template('login.html', form=form, login=True)


# class for users that stores their data in database
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email =  db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Tasks', backref='users')
    
    def __repr__(self) -> str:
        atributes = list(self.__dict__.items())[1:]
        return f'{type(self).__name__}(' + ', '.join(f'{k}={v}' for k, v in atributes) + ')'


class Tasks(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    importance = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(600))
    owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due = db.Column(db.String(20))
    time = db.Column(db.String(20))
    done = db.Column(db.Integer)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
