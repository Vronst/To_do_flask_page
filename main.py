import os
import smtplib
from datetime import datetime
from time import time

import bleach
from dotenv import load_dotenv
from flask import (
    Flask, render_template, redirect, request, session, url_for, flash, render_template_string
)
from flask_ckeditor import CKEditor
from flask_login import (
    UserMixin, login_user, LoginManager, current_user, login_required, logout_user
)
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import and_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.exc import UnmappedInstanceError
from werkzeug.security import generate_password_hash, check_password_hash

from forms import (RegisterForm, LoginForm, ToDoForm, SettingsForm, ResetForm,
                   ResetPassword, PasswordChange)

# globals with colors for tasks with different importance
task1 = '#adff2f'
task2 = '#ffff00'
task3 = '#fd3b3b'

EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')
SALT = os.environ.get('SALT')

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

# needed to activate account
SER = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.errorhandler(401)
def handle_method_not_allowed(e):
    # Redirect to index route if user tries to access forbidden sites
    return redirect(url_for('index'))

# below are routes that the user can take and benith them are databases

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
            flash('Default settings restored')
            return redirect(url_for('settings'))
        else:
            if form.validate():
                print('validated')
                cs.task1 = form.task1.data
                cs.task2 = form.task2.data
                cs.task3 = form.task3.data
                db.session.commit()
                flash('Applied changes!')
                return redirect(url_for('settings'))
    return render_template('settings.html', colors=(cs.task1, cs.task2, cs.task3), form=form,\
        logged=current_user.is_authenticated, reset=reset)


def validate_task(form, task=None):
    """
    validates form for task - its purpose is to omit redundant lines of code in add_task().
    it takes form and task as arguments and if task is none, adds new task else edit already exsiting (the one provided).
    this method returns 1 or 0 so the calling funcion knows if validation was a succes (1 means success, 0 fail)
    """
    if not task:
        if form.validate_on_submit():
            task = Tasks(importance=form.importance.data, 
                    name=form.task.data, description=form.task_description.data,
                        owner=current_user.get_id(), due=form.due.data, time=str(datetime.now()).split('.')[0])
            db.session.add(task)
            db.session.commit()
            return 1

    else:
        if form.validate_on_submit():
            task.importance = form.importance.data
            task.name = form.task.data
            task.description = form.task_description.data
            task.due = form.due.data
            task.time = str(datetime.now()).split('.')[0]
            db.session.commit()
            return 1
    return 0


@app.route('/add', methods=['GET', 'POST'])
@app.route('/edit/<int:task_id>', methods=['POST', 'GET'])
@login_required
def add_task(task_id=None):
    """
    not only allows user to add new tasks, it is also used to edit existing ones (see separate routes).
    If task_id was provided it searches for task and edit it else adds new one
    """
    task=None
    if not task_id:
        form = ToDoForm()
    else:
        try:
            task=db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()
            form = ToDoForm(task=task.name, importance=task.importance,\
                task_description=task.description, due=datetime.strptime(task.due, '%Y-%m-%d').date(), time=str(datetime.now()).split('.')[0])
        except AttributeError:
            flash('Task with provided ID does not exists')
            return redirect(url_for('index'))
    # checking if form was validated and if redirecting to index else add_task    
    return redirect(url_for('index'))\
        if validate_task(form, task=task) else\
            render_template('add_task.html', form=form, logged=current_user.is_authenticated, edit=task_id)


@app.route('/delete-id/<int:task_id>')
@login_required
def delete_task(task_id=None):
    try:
        task = db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()
        db.session.delete(task)
        db.session.commit()
    except UnmappedInstanceError:
        flash('Task with provided ID does not exists')
    return redirect(url_for('index'))


@app.route('/done-change')
@login_required
def done_change():
    session['done'] = not session.get('done', False)
    return redirect(url_for('index'))


@app.route('/')
@app.route('/<int:task_id>/')
def index(task_id=None):
    tasks = []
    
    # changing status done from 0 to 1 or from 1 to 0
    if task_id:
        try:
            task = db.session.execute(db.select(Tasks).where(Tasks.id == task_id)).scalar()
            task.done = False if task.done else True
            db.session.commit()
        except AttributeError:
            flash('Task with provided ID does not exists')

        # redirecting so we don't have to write all the parameters
        return redirect(url_for('index'))
    
    # getting tasks
    tasks = db.session.execute(db.select(Tasks).where(and_(Tasks.owner == current_user.get_id(), Tasks.done == session.get('done', False)))).scalars().all()
    
    # cleaning post from HTML code
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
                           user=current_user, tasks=sanitized_tasks, done=session.get('done', False),
                           colors=colors)


def generate_conf_token(email: str):
    return SER.dumps(email, salt=SALT)


def genereate_url_confirm(email: str, url: str = 'confirm'):
    token = generate_conf_token(email=email)
    # should use external so users can acces it from email
    return url_for(url, token=token, _external=True)


def send_reg_email(email):
    link = genereate_url_confirm(email)
    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(
            from_addr=EMAIL,
            to_addrs=email,
            msg=f"Subject: ToDO - Email authorization\n\n"
            f'Click this link to activate your account:\n\n{link}\n\n'
            f'If you did not make any account on our website please ignore this message'            
        )
        

def reset_pass_email(email):
    link = genereate_url_confirm(email, url='change_password')
    try:
        if session['send-reset-to-'+email] - time() < 3600:
            flash('Too early to send another email. Try again soon')
            return redirect(url_for('login'))
    except KeyError:
        pass
    
    session['send-reset-to-'+email] = time()
    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(
            from_addr=EMAIL,
            to_addrs=email,
            msg=f"Subject: ToDO - Password reset\n\n"
            f'Click this link to reset your password:\n\n{link}\n\n'
            f'If you did not started this procedure please ignore this message'            
        )
    flash('Email was send if account exists') 
    return redirect(url_for('login'))
        

@app.route('/reset-password', methods=['POST', 'GET'])
def reset_pass():
    form = ResetPassword()
    if form.validate_on_submit():
        return reset_pass_email(form.email.data)
    return render_template('reset_pass.html', form=form)    


@app.route('/change-password/<token>', methods=['POST', 'GET'])
@app.route('/change-password', methods=['POST', 'GET'])
def change_password(token=None):
    try:
        # max_age is checking if token is not older than 1h
        email = SER.loads(token, salt=SALT, max_age=3600) if token else current_user.email
    except SignatureExpired:
        flash('Link expired')
        return redirect(url_for('login'))
    form = PasswordChange()
    try:
        if form.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == email)).scalar()
            if token or check_password_hash(user.password, form.old_password.data):
                new_pass = generate_password_hash(form.password.data)
                user.password = new_pass
                db.session.commit()
                flash('Password has been changed')
                return redirect(url_for('login')) if token else redirect(url_for('settings'))
            else:
                flash('Old password is inccorect')
    except AttributeError as e:
        print(e)
        flash('Something went wrong')
    return render_template('change_pass.html', token=token, form=form)
    
        
    


@app.route('/confirm/<token>')
def confirm(token):
    email = SER.loads(token, salt=SALT)
    user = db.session.execute(db.select(User).where(User.email == email)).scalar()
    user.confirmed = True
    db.session.add(UserSettings(task1=task1, task2=task2, task3=task3, owner=user.get_id()))
    db.session.commit()
    return redirect(url_for('login'))     


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
        send_reg_email(user.email)
        flash('Activate your account before login!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, register=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # blocks logged-in users from logging again
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar()
            if not user.confirmed:
                flash('Confirm email before logging')
                send_reg_email(user.email)
                return render_template('login.html', form=form)
        except AttributeError:
            pass
        try:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('index'))
            else:
                flash('Wrong password or email')
        except AttributeError:
            flash('Wrong password or email')

    return render_template('login.html', form=form)


# class for users that stores their data in database
class User(UserMixin, db.Model):
    
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email =  db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    tasks = db.relationship('Tasks', backref='users')
    settings = db.relationship('UserSettings', backref='users')
    
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
    done = db.Column(db.Boolean, default=False)
    
    
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
