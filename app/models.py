from flask import current_app

import arrow
import phonenumbers

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
