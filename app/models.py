from flask import current_app, render_template
from twilio.rest import TwilioRestClient

import arrow
import phonenumbers

from .email import send_email

client = TwilioRestClient()

class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_url, timestamp):
        self.from_number = phonenumbers.parse(from_number)
        self.transcription = transcription
        self.recording_url = recording_url
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
        # For now, WUPHF it
        send_email(voicemail=self)

        self.send_sms_notification()


    def send_sms_notification(self):
        """Send a SMS about a new voicemail"""

        body = render_template('new_voicemail.txt', voicemail=self)

        client.messages.create(
            body=body,  # Message body, if any
            to='+17036230231',
            from_='+12027653512',
        )
