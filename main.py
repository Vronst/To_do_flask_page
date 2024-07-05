from flask import Flask, render_template, redirect, url_for, flash
import smtplib
import os
from forms import RegisterForm, LoginForm, ToDoForm
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, login_required, logout_user

load_dotenv()


class Base(DeclarativeBase):
    pass


# configuring app then implementing login manager and database
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')

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


@app.route('/')
def index():
    return render_template('index.html', text="You need to be logged in to acces ToDO list!", home=True, logged=current_user.is_authenticated)


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
        return redirect(url_for('index'))
    return render_template('register.html', form=form, register=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # blocks logged users from logging again
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar()
        print(user)
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
    
    def __repr__(self) -> str:
        atributes = list(self.__dict__.items())[1:]
        return f'{type(self).__name__}(' + ', '.join(f'{k}={v}' for k, v in atributes) + ')'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
