from flask import current_app, render_template, url_for
from sqlalchemy.ext.serializer import loads, dumps

import phonenumbers
import qrcode

from . import db
from .email import send_email
from .utils import get_twilio_rest_client, lookup_number


# Star codes (used in initial setup)
STAR_CODES = {
    'Verizon Wireless': {
        'enable': '*71',
        'disable': '*73'
    }
}


class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True)
    carrier = db.Column(db.String(50))
    name = db.Column(db.String(100))
    call_forwarding_set = db.Column(db.Boolean(), default=False)

    def __init__(self, phone_number):
        self.phone_number = phone_number

        # Look up the carrier
        lookup_info = lookup_number(phone_number)
        self.carrier = lookup_info.carrier['name']

    def __repr__(self):
        return '<Mailbox %r>' % self.phone_number

    def get_call_forwarding_code(self):
        """Get the code our user should dial to enable call forwarding"""
        voicemail_number = phonenumbers.parse(current_app.config['TWILIO_PHONE_NUMBER'])
        return '{0}{1}'.format(
            STAR_CODES[self.carrier]['enable'], voicemail_number.national_number)

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

        # Update the call_forwarding_set property if applicable
        if from_user and not self.call_forwarding_set:
            self.call_forwarding_set = True
            db.session.add(self)

        # Send contact info for our user to our caller
        contact_info = render_template(
            'contact_info.txt', mailbox=self, from_user=from_user,
            email_address=current_app.config['MAIL_USERNAME'],
            voicemail_number=current_app.config['TWILIO_PHONE_NUMBER'])

        client = get_twilio_rest_client()
        client.messages.create(
            body=contact_info,
            to=caller_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

    def generate_qr_code(self):
        """Generate a QR code which represents this Mailbox"""
        # Serialize this Mailbox
        serialized = dumps(self)

        # Make a QR code out of it
        return qrcode.make(serialized)

    def send_qr_code(self):
        """Sends a QR code with all our configuration to our user"""
        client = get_twilio_rest_client()

        client.messages.create(
            body="By the way, here's a QR code",
            to=self.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            media_url=url_for('main.qr_code', _external=True)
        )

    @classmethod
    def import_qr_code(cls):
        """Replaces any Mailbox in the database with one from the QR code"""
        pass


class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_sid):
        self.from_number = from_number
        self.transcription = transcription
        self.recording_sid = recording_sid

    def send_notification(self):
        """Notify our user that they have a new voicemail"""
        # Send a notification for each method that's configured
        if current_app.config['SMS_NOTIFICATIONS']:
            self.send_sms_notification()

        if current_app.config['EMAIL_NOTIFICATIONS']:
            send_email(voicemail=self)

    def send_sms_notification(self):
        """Send a SMS about a new voicemail"""

        body = render_template('notifications/new_voicemail.txt', voicemail=self)

        # Send the text message
        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=current_app.config['PHONE_NUMBER'],
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )
