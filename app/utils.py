from flask import current_app, render_template
from twilio.rest import TwilioRestClient
from twilio.rest.lookups import TwilioLookupsClient

import phonenumbers


def get_twilio_rest_client():
    client = TwilioRestClient(current_app.config['TWILIO_ACCOUNT_SID'],
                              current_app.config['TWILIO_AUTH_TOKEN'])
    return client

def get_twilio_lookup_client():
    client = TwilioLookupsClient(current_app.config['TWILIO_ACCOUNT_SID'],
                              current_app.config['TWILIO_AUTH_TOKEN'])
    return client

def lookup_number(phone_number):
    """Looks up a phone number to determine if it can receive a SMS message"""
    client = get_twilio_lookup_client()

    number_info = client.phone_numbers.get(phone_number,
                                           include_carrier_info=True)

    return number_info

def send_contact_info(phone_number):
    """Sends a caller some text and email information"""
    client = get_twilio_rest_client()

    user_number = phonenumbers.parse(current_app.config['PHONE_NUMBER'])
    local_format = phonenumbers.format_number(
            user_number, phonenumbers.PhoneNumberFormat.NATIONAL)

    contact_info = render_template(
        'contact_info.txt', phone_number=local_format,
        email_address=current_app.config['MAIL_USERNAME'])

    client.messages.create(
        body=contact_info,
        to=phone_number,
        from_=current_app.config['TWILIO_PHONE_NUMBER']
    )
