from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, FileField, SelectMultipleField, DecimalField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from wtforms.widgets import ListWidget, CheckboxInput
from flask_wtf.file import FileAllowed

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class MerchandiseForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    information = TextAreaField('Information', validators=[DataRequired(), Length(max=500)])
    value = DecimalField('Value (SEK)', validators=[DataRequired(), NumberRange(min=0)], places=2)
    specification = TextAreaField('Specification', validators=[DataRequired(), Length(max=500)])
    image = FileField('Image')
    category = SelectMultipleField('Category', choices=[
        ('T-Shirt', 'T-Shirt'),
        ('Hats', 'Hats'),
        ('Bags', 'Bags'),
        ('Hoodie', 'Hoodie'),
        ('More', 'More'),
        ('Other', 'Other')
    ])
    colors = SelectMultipleField('Colors', choices=[
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('black', 'Black'),
        ('white', 'White'),
        ('Yellow', 'Yellow')
    ])
    sizes = SelectMultipleField('Sizes', choices=[
        ('XS', 'X-Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'X-Large'),
        ('XXL', 'XL-Large')
    ])
    submit = SubmitField('Add Item')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class DiscountForm(FlaskForm):
    code = StringField('Discount Code', validators=[DataRequired()])
    percentage = FloatField('Discount Percentage', validators=[DataRequired(), NumberRange(min=0, max=100)])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Discount')

class EmployeeForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    submit = SubmitField('Register Employee')
