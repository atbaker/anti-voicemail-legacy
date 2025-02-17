from flask import current_app, redirect, render_template, request, url_for
from twilio import twiml

from . import voice
from ..decorators import validate_twilio_request
from ..models import Mailbox, Voicemail
from ..utils import get_twilio_rest_client, look_up_number


MISCONFIGURED = """This phone number cannot receive voicemails right now.
                Goodbye"""
UNABLE_TO_ANSWER = """{0} is unable to answer the phone. The best way to
                   reach them is by text message or email."""
SENDING_MESSAGE = """I am sending you a text message with {0}'s phone number,
                  email address, and voicemail number. Thank you."""
TEXT_EMAIL = """{0} will receive text messages you send to this number.
                You can email them at {1}"""
GATHER_CONFIRM = """If you would still like to leave {0} a voicemail,
                 press 1"""


@voice.route('/call', methods=['POST'])
@validate_twilio_request
def incoming_call(retry=False):
    """
    Receives incoming calls to our Twilio number, including calls that our
    user's carrier forwarded to our Twilio number
    """
    # If this caller called in the last 30 minutes, send them straight to the
    # record view
    caller = request.form['From']
    if current_app.cache.get(caller) and not retry:
        return redirect(url_for('voice.record'))

    # Start our TwiML response
    resp = twiml.Response()

    # Get our mailbox (if it's configured)
    mailbox = Mailbox.query.first()

    if mailbox is None or not mailbox.email:
        # This mailbox doesn't exist / isn't configured: end the call
        resp.say(MISCONFIGURED, voice='alice')
        return str(resp)

    elif caller in mailbox.whitelist:
        # If the caller is on our whitelist, send them to the record view
        return redirect(url_for('voice.record'))

    resp.say(UNABLE_TO_ANSWER.format(mailbox.name), voice='alice')

    # Look up what type of phone the caller is using
    caller_info = look_up_number(caller)

    # If we think the caller is on a mobile phone, send them a text message
    # with our user's contact info
    if caller_info and caller_info.carrier[
            'type'] == 'mobile' and caller_info.carrier['name']:
        resp.say(SENDING_MESSAGE.format(mailbox.name), voice='alice')
        if not retry:
            mailbox.send_contact_info(caller)

        # Add this phone number to our cache of recent callers
        current_app.cache.set(caller, True, timeout=30 * 60)
        return str(resp)

    resp.say(TEXT_EMAIL.format(mailbox.name, mailbox.email), voice='alice')

    # Ask the caller if they *really* need to leave a voicemail
    resp.pause(length=1)
    with resp.gather(numDigits=1, action=url_for('voice.record')) as g:
        g.say(GATHER_CONFIRM.format(mailbox.name), voice='alice')

    # Hang up if they don't enter any digits
    resp.say('Thank you for calling. Goodbye.', voice='alice')

    return str(resp)


@voice.route('/record', methods=['GET', 'POST'])
def record():
    """Ugh... someone wants to leave a voicemail."""
    resp = twiml.Response()

    # If a Digits attribute is present, make sure it's a value of 1
    if 'Digits' in request.form and request.form['Digits'] != '1':
        resp.say(
            'Thank you for not leaving a voicemail. Goodbye.',
            voice='alice')
        return str(resp)

    # Otherwise, begrudgingly let them leave a voicemail
    resp.say('You may now leave a message after the beep.', voice='alice')

    # Record and transcribe their message
    resp.record(action=url_for('voice.hang_up'), transcribe=True,
                transcribeCallback=url_for('voice.send_notification'))

    return str(resp)


@voice.route('/hang-up', methods=['POST'])
def hang_up():
    """
    Ends a call.
    """
    resp = twiml.Response()

    resp.say('Your message has been recorded. Goodbye.', voice='alice')
    resp.hangup()

    return str(resp)


@voice.route('/send-notification', methods=['POST'])
def send_notification():
    """Receives a transcribed voicemail from Twilio and sends an email"""
    # Create a new Voicemail from the POST data
    voicemail = Voicemail(
        request.form['From'], request.form.get(
            'TranscriptionText', '(transcription failed)'),
        request.form['RecordingSid'])

    voicemail.send_notification()

    # Be a nice web server and tell Twilio we're all done
    return ('', 204)


@voice.route('/recording/<recording_sid>')
def view_recording(recording_sid):
    """A small web page for listening to a recording"""
    # Retrieve the recording and transcription from Twilio
    client = get_twilio_rest_client()

    recording = client.recordings.get(recording_sid)
    transcription = recording.transcriptions.list()[0].transcription_text
    call = client.calls.get(recording.call_sid)

    return render_template('voice/recording.html', recording=recording,
                           transcription=transcription, call=call)
