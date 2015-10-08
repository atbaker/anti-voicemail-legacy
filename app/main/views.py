from flask import current_app, url_for, render_template, request
from flask_mail import Message
from twilio import twiml

from . import main
from .. import db
from ..models import Mailbox, Voicemail
from ..utils import get_twilio_rest_client, lookup_number


@main.route('/')
def index():
    return 'foo'

@main.route('/voicemail', methods=['POST'])
def incoming_call():
    """Ugh... someone wants to leave a voicemail..."""
    resp = twiml.Response()

    # Check if this call was forwarded from our main phone or was direct
    # to our Twilio number
    if 'ForwardedFrom' in request.form:
        # First, make sure this is a call for a mailbox that's configured
        mailbox = Mailbox.query.filter_by(phone_number=request.form['ForwardedFrom']).first()

        if mailbox is None:
            # This mailbox doesn't exist - end the call
            resp.say('This phone number cannot receive voicemails right now. Goodbye')
            return str(resp)

        resp.say('{0} is unable to answer the phone. The best way to \
            reach them is by text message or email.'.format(mailbox.name))

        # Look up what type of phone the caller is using
        caller = request.form['From']
        caller_info = lookup_number(caller)

        # If the caller is on a mobile phone, offer to send them a text message
        # with a phone number and email address
        # (also check that the carrier has a name so we're extra sure they
        # can receive text messages)
        if caller_info.carrier['type'] == 'mobile' and caller_info.carrier['name']:
            resp.say("I am sending you a text message with {0}'s phone number, \
                email address, and voicemail number. Thank you.".format(mailbox.name))
            mailbox.send_contact_info(caller)
            return str(resp)
        else:
            resp.say("{0} will receive text messages you send to this number. \
                You can email them at {1}".format(mailbox.name, current_app.config['MAIL_USERNAME']))

    # Begrudgingly let them leave a voicemail
    resp.say('You may now leave a message after the beep.')

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
    """Receives a transcribed voicemail from Twilio and sends an email"""
    # Create a new Voicemail from the POST data
    voicemail = Voicemail(request.form['From'],
                          request.form.get('TranscriptionText', '(transcription failed)'),
                          request.form['RecordingSid'])

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

@main.route('/sms', methods=['POST'])
def sms_message():
    """Receives an SMS message from a number"""
    from_number = request.form['From']
    # See if we have a Mailbox for this number
    mailbox = Mailbox.query.filter_by(phone_number=from_number).first()

    if mailbox is None:
        # Make sure we don't have another mailbox already
        if Mailbox.query.count() > 0:
            # We're single-tenant for now, so don't make any more mailboxes
            return ('', 204)

        # Make a mailbox for this number
        new_mailbox = Mailbox(from_number)
        db.session.add(new_mailbox)

        # Ask the user what their name is
        new_mailbox.ask_name()
    elif not mailbox.name:
        # If we have a mailbox but don't have a name, assume this message
        # contains the user's name
        mailbox.name = request.form['Body']
        db.session.add(mailbox)

        # Tell the user we're all done with setup
        mailbox.notify_setup_complete()
    else:
        # We have no idea why the user is texting us
        mailbox.i_have_no_idea_what_im_doing()

    # Be a nice web server and tell Twilio we're all done
    return ('', 204)
