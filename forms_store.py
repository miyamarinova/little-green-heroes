from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import Form, IntegerField, StringField,SubmitField, BooleanField,PasswordField, TextAreaField, validators,SelectField
from flask_wtf import FlaskForm

class AddproductForm(FlaskForm):
    name = StringField('Name', [validators.DataRequired()])
    price = IntegerField('Price', [validators.DataRequired()])
    description = TextAreaField('Description', [validators.DataRequired()])
    image_1 = FileField('Image 1', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'])])

class CustomerRegisterForm(FlaskForm):
    name = StringField('Name: ')
    username = StringField('Username: ',[validators.DataRequired()])
    email = StringField('Email: ', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password: ', [validators.DataRequired(),validators.EqualTo('confirm',message="Both password must be the same!")])
    confirm = PasswordField('Confirm Password', [validators.DataRequired()])
    country = StringField('Conutry: ',[validators.DataRequired()])
    state = StringField('State: ', [validators.DataRequired()])
    city = StringField('City: ', [validators.DataRequired()])
    zipcode = StringField('Zip code: ', [validators.DataRequired()])
    address = StringField('Address: ', [validators.DataRequired()])
    phone = StringField('Phone: ',[validators.DataRequired()])

    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField("Email", [validators.DataRequired()])
    password = PasswordField("Password", [validators.DataRequired()])
    log_in = SubmitField('Log In')

