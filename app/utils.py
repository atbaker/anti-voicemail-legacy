from flask import current_app
from twilio.rest import TwilioRestClient


def get_twilio_rest_client():
    client = TwilioRestClient(current_app.config['TWILIO_ACCOUNT_SID'],
                              current_app.config['TWILIO_AUTH_TOKEN'])
    return client
