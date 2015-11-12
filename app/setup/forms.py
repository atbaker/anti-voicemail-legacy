from wtforms import Form, StringField, validators

import phonenumbers


class EmailForm(Form):
    """Validates email input"""
    email = StringField('Email address', validators=[validators.Email()])

def validate_phone_number(form, field):
    """Validates that a phone number is valid"""
    try:
        # Parse the number using the default region code provided
        parsed_number = phonenumbers.parse(field.data, form.default_region_code.data)

        if not phonenumbers.is_valid_number(parsed_number):
            raise validators.ValidationError('Invalid phone number')

        # Update the field's data to be an E164 formatted version of the number
        field.data = phonenumbers.format_number(
            parsed_number,
            phonenumbers.PhoneNumberFormat.E164)

    except phonenumbers.phonenumberutil.NumberParseException:
        raise validators.ValidationError('Invalid phone number')

class PhoneNumberForm(Form):
    """Validates phone number input"""
    phone_number = StringField('Phone number', validators=[validate_phone_number])
    default_region_code = StringField('Default region code')
