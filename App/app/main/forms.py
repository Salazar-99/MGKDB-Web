from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, RadioField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Length, Email, Optional
import re

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=12)])
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

#TODO: Update filter form to new filters
class FilterForm(FlaskForm):
    collection = RadioField('Run Type:', choices=[('LinearRuns', 'Linear Runs'), ('NonlinRuns', 'Non-linear Runs')], validators=[DataRequired()])
    id = StringField('Run ID', id='id')
    #id corresponds to actual name of field in the db, used to generate filters
    gamma_max = DecimalField(label="gamma_max", id="QoI.gamma(cs/a)", validators=[Optional()])
    gamma_min = DecimalField(label="gamma_min", id="QoI.gamma(cs/a)", validators=[Optional()])
    omega_max = DecimalField(label="omega_max", id="QoI.omega(cs/a)", validators=[Optional()])
    omega_min = DecimalField(label="omega_min", id="QoI.omega(cs/a)", validators=[Optional()])
    z_max = DecimalField(label="z_max", id="QoI.<z>", validators=[Optional()])
    z_min = DecimalField(label="z_min", id="QoI.<z>", validators=[Optional()])
    lambda_z_max = DecimalField(label="lambda_z_max", id="QoI.lambda_z", validators=[Optional()])
    lambda_z_min = DecimalField(label="lambda_z_min", id="QoI.lambda_z", validators=[Optional()])
    submit = SubmitField('Search')

class PageForm(FlaskForm):
    page = IntegerField('Page')
    submit = SubmitField('Go')



