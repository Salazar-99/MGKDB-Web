from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, RadioField, DecimalField
from wtforms.validators import DataRequired, Length, Email
import re

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    verify_password = PasswordField('Verify Password', validators=[DataRequired()])
    role = RadioField('Role', choices=[('researcher', 'Researcher'), ('student', 'Student'), ('other', 'Other')])
    reason = StringField('Reason For Requesting An Account', 
                            validators=[DataRequired(), 
                                        Length(min=10, max=128, message='Reason must be between 10 and 128 characters.')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class FilterForm(FlaskForm):
    collection = RadioField('Run Type', choices=[('linear', 'LinearRuns'), ('nonlinear', 'NonlinRuns')])
    gamma_max = DecimalField()
    gamma_min = DecimalField()
    omega_max = DecimalField()
    omega_min = DecimalField()
    z_max = DecimalField()
    z_min = DecimalField()
    lambda_z_max = DecimalField()
    lambda_z_min = DecimalField()
    submit = SubmitField('Search')



