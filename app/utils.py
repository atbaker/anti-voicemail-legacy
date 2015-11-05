from flask import current_app, render_template, url_for
from time import sleep
from twilio.rest import TwilioRestClient
from twilio.rest.exceptions import TwilioRestException
from twilio.rest.lookups import TwilioLookupsClient

import phonenumbers


def get_twilio_rest_client():
    """Instantiates a Twilio REST Client"""
    client = TwilioRestClient(current_app.config['TWILIO_ACCOUNT_SID'],
                              current_app.config['TWILIO_AUTH_TOKEN'])
    return client

def send_async_message(app, body, to_number, delay=30):
    """Used to send text messages asynchronously in a Thread"""
    # Sleep (if specified)
    sleep(delay)

    with app.app_context():
        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=to_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

def look_up_number(phone_number):
    """Looks up a phone number to determine if it can receive a SMS message"""
    client = TwilioLookupsClient(current_app.config['TWILIO_ACCOUNT_SID'],
                                 current_app.config['TWILIO_AUTH_TOKEN'])

    try:
        number_info = client.phone_numbers.get(phone_number,
                                               include_carrier_info=True)
    except TwilioRestException:
        number_info = None

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
        update_kwargs['voice_url'] = url_for('voice.incoming_call', _external=True)
    if not twilio_number.sms_url:
        update_kwargs['sms_url'] = url_for('setup.incoming_sms', _external=True)

    # Also set the fallback urls
    if not twilio_number.voice_fallback_url:
        update_kwargs['voice_fallback_url'] = current_app.config['VOICE_FALLBACK_URL']
    if not twilio_number.sms_fallback_url:
        update_kwargs['sms_fallback_url'] = current_app.config['SMS_FALLBACK_URL']

    # If we added any kwargs to our dict, update those properties on the number
    if update_kwargs:
        twilio_number.update(**update_kwargs)

def gruber_quote(): # pragma: no cover
    """Sends an inspirational quote to the user when the server is stopped"""
    gruber = """
    And when Alexander saw the breadth of his domain,
        he wept for there were no more worlds to conquer.
                                —Hans Gruber (1988)"""

    # Don't use real logging because we *always* want the user to see it
    print(gruber)

import atexit
import sys
if sys.argv[-1] == 'test': # pragma: no cover
    atexit.register(gruber_quote)
