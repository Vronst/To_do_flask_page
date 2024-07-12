from wtforms import DateField, StringField, SubmitField,\
    EmailField, PasswordField, BooleanField, RadioField, ColorField
from wtforms.validators import DataRequired, Email, Length, EqualTo
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
    repeat_pass = PasswordField(label='Repeat password: ', validators=[DataRequired(), EqualTo('password', message='Passwords must match!')])
    submit = SubmitField("Register")
    

class ToDoForm(FlaskForm):
    task = StringField(label='Task name: ', validators=[DataRequired()])
    importance = RadioField(choices=[1, 2, 3])
    due = DateField('Has to be completed due to:', format='%Y-%m-%d')
    task_description = CKEditorField(label='Description: ')   
    submit = SubmitField()


class SettingsForm(FlaskForm):
    task1 = ColorField(label='Color for importance 1:')
    task2 = ColorField(label='Color for importance 2:')
    task3 = ColorField(label='Color for importance 3:')
    submit = SubmitField('Apply')
    
    
class ResetForm(FlaskForm):
    submit = SubmitField('Reset to defaults')

