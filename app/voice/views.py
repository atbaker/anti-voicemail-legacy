from flask import redirect, render_template, request, url_for
from twilio import twiml

from . import voice
from ..decorators import validate_twilio_request
from ..models import Mailbox, Voicemail
from ..utils import get_twilio_rest_client, look_up_number


@voice.route('/call', methods=['POST'])
@validate_twilio_request
def incoming_call():
    """
    Receives incoming calls to our Twilio number, including calls that our
    user's carrier forwarded to our Twilio number
    """
    # If this call was directly to our Anti-Voicemail number, send them to the
    # voicemail view
    if 'ForwardedFrom' not in request.form:
        return redirect(url_for('voice.record'))

    resp = twiml.Response()

    # Get our mailbox (if it's configured)
    mailbox = Mailbox.query.filter_by(phone_number=request.form['ForwardedFrom']).first()

    if mailbox is None or not mailbox.email:
        # This mailbox doesn't exist / isn't configured: end the call
        resp.say('This phone number cannot receive voicemails right now. Goodbye', voice='alice')
        return str(resp)
    elif request.form['From'] in mailbox.whitelist:
        # If the caller is on our whitelist, send them to the record view
        return redirect(url_for('voice.record'))

    resp.say('{0} is unable to answer the phone. The best way to \
        reach them is by text message or email.'.format(mailbox.name),
        voice='alice')

    # Look up what type of phone the caller is using
    caller = request.form['From']
    caller_info = look_up_number(caller)

    # If we think the caller is on a mobile phone, send them a text message
    # with our user's contact info
    if caller_info and caller_info.carrier['type'] == 'mobile' and caller_info.carrier['name']:
        resp.say("I am sending you a text message with {0}'s phone number, \
            email address, and voicemail number. Thank you.".format(mailbox.name),
            voice='alice')
        mailbox.send_contact_info(caller)
        return str(resp)

    contact_info = "{0} will receive text messages you send to this number. You can email them at {1}".format(mailbox.name, mailbox.email)
    resp.say(contact_info, voice='alice')

    # Ask the caller if they *really* need to leave a voicemail
    resp.pause(length=1)
    with resp.gather(numDigits=1, action=url_for('voice.record')) as g:
        g.say('If you would still like to leave {0} a voicemail, press 1'.format(mailbox.name),
            voice='alice')

    # Hang up if they don't enter any digits
    resp.say('Thank you for calling. Goodbye.', voice='alice')

    return str(resp)

@voice.route('/record', methods=['GET', 'POST'])
def record():
    """Ugh... someone wants to leave a voicemail."""
    resp = twiml.Response()

    # If a Digits attribute is present, make sure it's a value of 1
    if 'Digits' in request.form and request.form['Digits'] != '1':
        resp.say('Thank you for not leaving a voicemail. Goodbye.', voice='alice')
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
    voicemail = Voicemail(request.form['From'],
                          request.form.get('TranscriptionText', '(transcription failed)'),
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

    return render_template('voice/recording.html', recording=recording, transcription=transcription, call=call)
