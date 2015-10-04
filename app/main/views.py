from flask import url_for, render_template, request
from flask_mail import Message
from twilio import twiml

import arrow

from . import main
from ..models import Voicemail
from ..utils import get_twilio_rest_client


@main.route('/')
def index():
    import pdb; pdb.set_trace()
    return 'foo'

@main.route('/voicemail', methods=['POST'])
def record_voicemail():
    """Record a new voicemail"""
    resp = twiml.Response()

    # Tell the caller they reached the voicemail
    resp.say('Andrew Baker is unable to answer the phone. Please leave a \
              message after the beep.')

    # Record and transcribe their message
    now = arrow.utcnow()
    resp.record(action=url_for('main.hang_up'), transcribe=True,
                transcribeCallback=url_for('main.send_notification', timestamp=now.timestamp))

    return str(resp)

@main.route('/hang-up', methods=['POST'])
def hang_up():
    """
    Ends a call. Only used when a caller has been droning on for more than
    two minutes.
    """
    resp = twiml.Response()

    resp.say('Your message has been recorded. Goodbye.')
    resp.hangup()

    return str(resp)

@main.route('/send-notification', methods=['POST'])
def send_notification():
    """Receives a transcribed voicemail from Twilio and sends an email"""
    # Create a new Voicemail from the POST data
    voicemail = Voicemail(request.form['From'],
                          request.form.get('TranscriptionText', '(transcription failed)'),
                          request.form['RecordingSid'],
                          request.args['timestamp'])

    voicemail.send_notification()

    # Be a nice web server and tell Twilio we're all done
    return ('', 204)

@main.route('/recording/<recording_sid>')
def view_recording(recording_sid):
    """A small web page for listening to a recording"""
    # Retrieve the recording metadata from Twilio
    client = get_twilio_rest_client()
    recording = client.recordings.get(recording_sid)

    mp3_url = recording.formats['mp3']

    return render_template('recording.html', recording_url=mp3_url)
