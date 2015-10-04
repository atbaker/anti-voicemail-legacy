from flask import current_app, render_template

import arrow
import phonenumbers

from .email import send_email
from .utils import get_twilio_rest_client


class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_sid, timestamp):
        self.from_number = phonenumbers.parse(from_number)
        self.transcription = transcription
        self.recording_sid = recording_sid
        self.timestamp = arrow.get(timestamp)

    def get_national_format(self):
        """Provides a nicer format of the from_number"""
        return phonenumbers.format_number(
            self.from_number, phonenumbers.PhoneNumberFormat.NATIONAL)

    def get_local_time(self):
        """Converts the timestamp to local time"""
        local_time = self.timestamp.to(current_app.config['TIME_ZONE'])
        return local_time.format('hh:mm A')

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
