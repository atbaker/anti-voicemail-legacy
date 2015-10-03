from flask import current_app

import arrow

class Voicemail(object):
    """A simple class to represent a voicemail. Doesn't use a database"""

    def __init__(self, from_number, transcription, recording_url, timestamp):
        self.from_number = from_number
        self.transcription = transcription
        self.recording_url = recording_url
        self.timestamp = timestamp

    def get_local_time(self):
        utc_time = arrow.get(self.timestamp)
        local_time = utc_time.to(current_app.config['TIME_ZONE'])
        return local_time.format('hh:mm A')
