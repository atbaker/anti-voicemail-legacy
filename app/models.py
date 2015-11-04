from flask import current_app, render_template, url_for
from threading import Thread

import json
import phonenumbers
import qrcode
import requests

from . import db
from .utils import get_twilio_rest_client, look_up_number, send_async_message


# Star codes (used in initial setup)
STAR_CODES = {
    'AT&T Wireless': {
        'enable': '*004*{0}#',
        'disable': '##004#'
    },
    # Need to verify Sprint
    # 'Sprint Spectrum, L.P.': {
    #     'enable': '*28{0}',
    #     'disable': '*38'
    # },
    'T-Mobile USA, Inc.': {
        'enable': '*004*{0}#',
        'disable': '##004#'
    },
    'Verizon Wireless': {
        'enable': '*71{0}',
        'disable': '*73'
    }
}

class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True)
    carrier = db.Column(db.String(50))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    call_forwarding_set = db.Column(db.Boolean(), default=False)
    feelings_on_qr_codes = db.Column(db.String(15))

    def __init__(self, phone_number, id=None, carrier=None, name=None,
                 email=None, call_forwarding_set=None, feelings_on_qr_codes=None):
        # Get the carrier if none was provided
        if carrier is None:
            # Look up the carrier
            lookup_info = look_up_number(phone_number)
            carrier = lookup_info.carrier['name']

        self.id = id
        self.phone_number = phone_number
        self.carrier = carrier
        self.name = name
        self.email = email
        self.call_forwarding_set = call_forwarding_set
        self.feelings_on_qr_codes = feelings_on_qr_codes

    def __repr__(self):
        return '<Mailbox %r>' % self.phone_number

    def get_call_forwarding_code(self):
        """Get the code our user should dial to enable call forwarding"""
        voicemail_number = phonenumbers.parse(current_app.config['TWILIO_PHONE_NUMBER'])
        code = STAR_CODES[self.carrier]['enable'].format(voicemail_number.national_number)
        return code

    def get_disable_code(self):
        """
        Gets the code to disable call forwarding.

        See: https://www.youtube.com/watch?v=wagkBedzwI8
        """
        return STAR_CODES[self.carrier]['disable']

    def send_contact_info(self, caller_number):
        """Sends a caller some text and email information for this mailbox"""
        # Set an extra variable if the caller is our user
        from_user = caller_number == self.phone_number

        # Send contact info for our user to our caller
        contact_info = render_template(
            'voice/contact_info.txt', mailbox=self, from_user=from_user,
            voicemail_number=current_app.config['TWILIO_PHONE_NUMBER'])

        client = get_twilio_rest_client()
        client.messages.create(
            body=contact_info,
            to=caller_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

        # If this call is the user trying out Anti-Voicemail for the first time,
        # update the call_forwarding_set property and send them the config image
        if from_user and not self.call_forwarding_set:
            self.call_forwarding_set = True
            db.session.add(self)

            # Now ask them the big question
            # (unless we know it already from a previous restore)
            if not self.feelings_on_qr_codes:
                body = render_template('setup/ask_qr_codes.txt')
            else:
                body = render_template('setup/complete.txt')

            app = current_app._get_current_object()

            thread = Thread(target=send_async_message, args=[app, body, caller_number])
            thread.start()

    def generate_config_image(self):
        """Generate a QR code which represents this Mailbox"""
        # Serialize this Mailbox
        mailbox_dict = self.__dict__.copy()
        mailbox_dict['call_forwarding_set'] = False
        del mailbox_dict['_sa_instance_state']

        mailbox_json = json.dumps(mailbox_dict)

        # Make a QR code out of it
        return qrcode.make(mailbox_json)

    def send_config_image(self):
        """
        Sends a QR code image to our user which contains the configuration for
        this Mailbox
        """
        body = render_template('setup/complete.txt')

        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=self.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            media_url=url_for('setup.config_image', _external=True)
        )

    @classmethod
    def import_config_image(cls, config_image_url):
        """
        Replaces any Mailbox in the database with one from
        data stored in a config image
        """
        try:
            # Read the QR code using api.qrserver.com
            response = requests.get('https://api.qrserver.com/v1/read-qr-code/',
                                    params={'fileurl': config_image_url})

            # Get the QR data and convert it to bytes
            serialized = response.json()[0]['symbol'][0]['data']
            mailbox_dict = json.loads(serialized)

            # Load the serialized data
            mailbox = cls(**mailbox_dict)

            # Delete any existing Mailbox
            cls.query.delete()

            # Save the new Mailbox
            db.session.add(mailbox)

            # It worked! Let our user know they're good to go
            return render_template('setup/restore_config.txt', mailbox=mailbox)

        except Exception:
            # Something went wrong - this isn't going to work
            return "Ooops! I couldn't read that file after all. Sorry! D:"

class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_sid):
        self.from_number = from_number
        self.transcription = transcription
        self.recording_sid = recording_sid

        # Set a mailbox property also, for convenience
        self.mailbox = Mailbox.query.one()

    def send_notification(self):
        """Send a SMS about a new voicemail"""

        body = render_template('voice/new_voicemail.txt', voicemail=self)

        # Send the text message
        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=self.mailbox.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )
