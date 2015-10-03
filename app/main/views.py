from flask import url_for, request
from twilio import twiml

from . import main


@main.route('/')
def index():
    return 'foo'

@main.route('/voicemail', methods=['POST'])
def record_voicemail():
    """Record a new voicemail"""
    resp = twiml.Response()

    # Tell the caller they reached the voicemail
    resp.say('Andrew Baker is unable to answer the phone. Please leave a \
              message after the beep.')

    # Record and transcribe their message
    resp.record(action=url_for('main.hang_up'), transcribe=True,
                transcribeCallback=url_for('main.send_notification'))

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
    """Receives a transcribed voicemail from Twilio and sends a notification"""
    import pdb; pdb.set_trace()
