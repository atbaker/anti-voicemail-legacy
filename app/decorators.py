from flask import abort, current_app, request
from functools import wraps
from twilio.util import RequestValidator


def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(current_app.config['TWILIO_AUTH_TOKEN'])

        # If our app is using piggyback SSL, we'll need to change request.url
        # to be https instead of http because Twilio used https in its request
        url = request.url
        if 'X-Forwarded-Proto' in request.headers:
            url = request.url.replace('http',
                                      request.headers['X-Forwarded-Proto'])

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid (or we're testing)
        # Otherwise, return a 403 error if it's not
        if request_valid or (current_app.config['TESTING'] == True
                             and not request.headers.get('FORCE_VALIDATION', False)):
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function
