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
    collection = RadioField('Run Type:', choices=[('LinearRuns', 'Linear Runs'), ('NonlinRuns', 'Non-linear Runs')])
    #id corresponds to actual name of field in the db, used to generate filters
    gamma_max = DecimalField(label="gamma_max", id="QoI.gamma(cs/a)")
    gamma_min = DecimalField(label="gamma_min", id="QoI.gamma(cs/a)")
    omega_max = DecimalField(label="omega_max", id="QoI.omega(cs/a)")
    omega_min = DecimalField(label="omega_min", id="QoI.omega(cs/a)")
    z_max = DecimalField(label="z_max", id="QoI.<z>")
    z_min = DecimalField(label="z_min", id="QoI.<z>")
    lambda_z_max = DecimalField(label="lambda_z_max", id="QoI.lambda_z")
    lambda_z_min = DecimalField(label="lambda_z_min", id="QoI.lambda_z")
    submit = SubmitField('Search')



