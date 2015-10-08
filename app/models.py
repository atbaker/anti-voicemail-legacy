from flask import current_app, render_template

import phonenumbers

from . import db
from .email import send_email
from .utils import get_twilio_rest_client


class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))

    def __init__(self, phone_number, name=''):
        self.phone_number = phone_number
        self.name = name

    def __repr__(self):
        return '<Mailbox %r>' % self.phone_number

    def ask_name(self):
        """Asks the user what their name is"""
        body = render_template('setup/ask_name.txt')

        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=self.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

    def notify_setup_complete(self):
        """Tells the user that setup is complete"""
        body = render_template('setup/complete.txt', mailbox=self)

        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=self.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

    def i_have_no_idea_what_im_doing(self):
        """
        We have no idea why the user is texting us and wish they would leave us
        alone
        """
        body = render_template('setup/no_idea.txt', mailbox=self)

        client = get_twilio_rest_client()
        client.messages.create(
            body=body,
            to=self.phone_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )

    def send_contact_info(self, caller_number):
        """Sends a caller some text and email information for this mailbox"""
        phone_number = phonenumbers.parse(self.phone_number)
        local_format = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.NATIONAL)

        contact_info = render_template(
            'contact_info.txt', name=self.name, phone_number=local_format,
            email_address=current_app.config['MAIL_USERNAME'],
            voicemail_number=current_app.config['TWILIO_PHONE_NUMBER'])

        client = get_twilio_rest_client()
        client.messages.create(
            body=contact_info,
            to=caller_number,
            from_=current_app.config['TWILIO_PHONE_NUMBER']
        )


class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_sid):
        self.from_number = phonenumbers.parse(from_number)
        self.transcription = transcription
        self.recording_sid = recording_sid

    def get_national_format(self):
        """Provides a nicer format of the from_number"""
        return phonenumbers.format_number(
            self.from_number, phonenumbers.PhoneNumberFormat.NATIONAL)

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
