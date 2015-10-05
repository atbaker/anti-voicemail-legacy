from flask import url_for, render_template, request
from flask_mail import Message
from twilio import twiml

import arrow

from . import main
from ..models import Voicemail
from ..utils import get_twilio_rest_client, lookup_number, send_contact_info


@main.route('/')
def index():
    return 'foo'

@main.route('/voicemail', methods=['POST'])
def incoming_call():
    """Ugh... someone wants to leave a voicemail..."""
    caller = request.form['From']

    resp = twiml.Response()
    resp.say('Andrew Baker is unable to answer the phone. The best way to \
        reach them is by text message or email.')

    caller_info = lookup_number(caller)

    # If the caller is on a mobile phone, offer to send them a text message
    # with a phone number and email address
    # (also check that the carrier has a name so we're extra sure they
    # can receive text messages)
    if caller_info.carrier['type'] == 'mobile' and caller_info.carrier['name']:
        resp.say("I will send you a text message with Andrew's phone number \
            and email address. Goodbye")
        send_contact_info(caller)
    else:
        # Begrudgingly let them leave a voicemail
        resp.say('Next time please text or call Andrew. You may now leave \
            a message after the beep.')

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
