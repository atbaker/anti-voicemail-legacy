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

def convert_to_national_format(phone_number):
    """Converts an E.164 formatted number to a national format"""
    return phonenumbers.format_number(phonenumbers.parse(phone_number),
                                      phonenumbers.PhoneNumberFormat.NATIONAL)
