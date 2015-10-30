from flask import current_app, render_template, url_for
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

def set_twilio_number_urls():
    """
    Sets the voice_url and sms_url on our Twilio phone number to point to this
    application
    """
    client = get_twilio_rest_client()

    # Get our Twilio phone number
    numbers = client.phone_numbers.list(phone_number=current_app.config['TWILIO_PHONE_NUMBER'])
    twilio_number = numbers[0]

    update_kwargs = {}

    # Set the URLs only if they're blank (don't override any existing config)
    if not twilio_number.voice_url:
        update_kwargs['voice_url'] = url_for('main.incoming_call', _external=True)
    if not twilio_number.sms_url:
        update_kwargs['sms_url'] = url_for('main.incoming_sms', _external=True)

    # Also set the fallback urls
    if not twilio_number.voice_fallback_url:
        update_kwargs['voice_fallback_url'] = url_for('main.voice_error', _external=True)
    if not twilio_number.sms_fallback_url:
        update_kwargs['sms_fallback_url'] = url_for('main.sms_error', _external=True)

    # If we added any kwargs to our dict, update those properties on the number
    twilio_number.update(**update_kwargs)
