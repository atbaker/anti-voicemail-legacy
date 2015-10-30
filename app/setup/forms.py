from wtforms import Form, StringField, validators


class EmailForm(Form):
    """Validates email input"""
    email = StringField(u'Email address', validators=[validators.Email()])
