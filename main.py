from flask import Flask, render_template, request, session, redirect, url_for
import smtplib
import os
from forms import RegisterForm, LoginForm, ToDoForm
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')


@app.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', home=True)
    else:
        return render_template('index.html', text="You need to be logged in to acces ToDO list!", home=True)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # blocks logged users from registering
    if 'user' in session:
        return redirect(url_for('index'))
    form = RegisterForm()
    
    if form.validate_on_submit():
        name = form.nick.data
        print(name)
        # TODO: base with users to check for duplicates before registering
        return "123456"
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # blocks logged users from logging again
    if 'user' in session:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for('index'))
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
