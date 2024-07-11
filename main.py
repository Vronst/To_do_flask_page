from flask import Flask, render_template, redirect, request, url_for, flash, render_template_string
import smtplib
import os
from sqlalchemy import and_
from forms import RegisterForm, LoginForm, ToDoForm, SettingsForm, ResetForm
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user
from flask_ckeditor import CKEditor
from datetime import datetime
import bleach


# global for changing task that are showed (completed and uncompleted)
done = 0
# globals with colors for tasks with different importance
task1 = '#adff2f'
task2 = '#ffff00'
task3 = '#fd3b3b'

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


@app.route('/settings', methods=['GET', "POST"])
@login_required
def settings():
    # global task1, task2, task3
    cs = db.session.execute(db.select(UserSettings).where(UserSettings.owner == current_user.get_id())).scalar()
    form = SettingsForm(task1=cs.task1, task2=cs.task2, task3=cs.task3)
    reset = ResetForm()
    if request.method == 'POST':
        if 'Reset' in request.form['submit']:
            print('reset')
            cs.task1 = task1
            cs.task2 = task2
            cs.task3 = task3
            db.session.commit()
            return redirect(url_for('settings'))
        else:
            if form.validate():
                print('validated')
                cs.task1 = form.task1.data
                cs.task2 = form.task2.data
                cs.task3 = form.task3.data
                db.session.commit()
                return redirect(url_for('settings'))
    return render_template('settings.html', colors=(cs.task1, cs.task2, cs.task3), form=form,\
        logged=current_user.is_authenticated, reset=reset)


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


@app.route('/delete-id/<int:task_id>')
@login_required
def delete_task(task_id=None, done=True):
        task = db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()
        db.session.delete(task)
        db.session.commit()
        return redirect(url_for('index', done=done))


@app.route('/done-change')
@login_required
def done_change():
    
    global done
    done = 0 if done else 1
    return redirect(url_for('index'))


@app.route('/')
@app.route('/<int:task_id>/')
def index(task_id=None):
    tasks = []
    
    # changeing status done from 0 to 1 or from 1 to 0
    if task_id:
        task = db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()
        task.done = 0 if task.done else 1
        db.session.commit()
        # without redirection simple refreching will act as clicking same task again and again
        return redirect(url_for('index'))
    
    # getting tasks
    if done:
        tasks = db.session.execute(db.select(Tasks).where(and_(Tasks.owner == current_user.get_id(), Tasks.done == done))).scalars().all()
    else:
        tasks = db.session.execute(db.select(Tasks).where(and_(Tasks.owner == current_user.get_id(), Tasks.done == done))).scalars().all()
    # cleaning post from html code
    sanitized_tasks = []
    for task in tasks:
        task_dict = task.__dict__  # Convert task object to dictionary if it's a SQLAlchemy object
        sanitized_task = {key: bleach.clean(value, strip=True) if isinstance(value, str) else value for key, value in task_dict.items()}
        sanitized_tasks.append(sanitized_task)
    if current_user.is_authenticated:
        cs = db.session.execute(db.select(UserSettings).where(UserSettings.owner == current_user.get_id())).scalar()
        colors = (cs.task1, cs.task2, cs.task3)
    else:
        colors = (task1, task2, task3)
    return render_template('index.html', home=True, logged=current_user.is_authenticated,
                           user=current_user, tasks=sanitized_tasks, done=done,
                           colors=colors)


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
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        login_user(user)
        db.session.add(UserSettings(task1=task1, task2=task2, task3=task3, owner=user.get_id()))
        db.session.commit()
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
    settings= db.relationship('UserSettings', backref='users')
    
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
    
    
class UserSettings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task1 = db.Column(db.String(20))
    task2 = db.Column(db.String(20))
    task3 = db.Column(db.String(20))
    owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
