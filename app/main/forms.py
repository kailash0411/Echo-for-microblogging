from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Email, Length
from flask import request, current_app
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('User Name', validators=[DataRequired()])
    about_me = TextAreaField('Your Bio', validators=[Length(min=0, max=140)])
    submit = SubmitField('Save')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class EmptyForm(FlaskForm):
    submit = SubmitField('submit')

class PostForm(FlaskForm):
    post = TextAreaField('Any Thoughts....', validators=[
        DataRequired(), Length(min=1, max=4096)
    ])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    comment = TextAreaField('Comments', validators=[
        DataRequired(), Length(min=1, max=4096)
    ], render_kw={'style': 'max-width:500px'})
    submit = SubmitField('Comment')

class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)