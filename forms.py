from wtforms import StringField, SubmitField, EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):
    email = EmailField(label='Email: ', validators=[DataRequired(), Email("Invalid email address")])
    password = PasswordField(label='Password: ', validators=[DataRequired(), Length(min=8, message="Incorrect password or email")])
    remember = BooleanField(label='Remember me')
    submit = SubmitField("Log in")
    

class RegisterForm(FlaskForm):
    nick = StringField(label='Nick: ', validators=[DataRequired(),
                                                   Length(min=4, max=10, message="Nick must be 4-10 letter long")])
    email = EmailField(label='Email: ', validators=[DataRequired(),
                                                    Email("Invalid email address")])
    password = PasswordField(label='Password: ', validators=[DataRequired(),
                                                             Length(min=8, message="Password must be at least 8 letters long")])
    submit = SubmitField("Register")
    

class ToDoForm(FlaskForm):
    task = StringField(label='Task: ', validators=[DataRequired()])
    task_description = CKEditorField(label='Description: ')   
    submit = SubmitField()
