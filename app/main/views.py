from flask import current_app, send_file, url_for, render_template, request
from flask_mail import Message
from io import BytesIO
from twilio import twiml

from . import main
from .forms import EmailForm
from .. import db
from ..models import Mailbox, Voicemail
from ..utils import get_twilio_rest_client, lookup_number, set_twilio_number_urls


@main.route('/')
def index():
    # While we're rendering the homepage, do the user a favor and configure
    # their Twilio phone number callback URLs for them (if they haven't already)
    set_twilio_number_urls()

    return render_template('index.html', twilio_number=current_app.config['TWILIO_PHONE_NUMBER'])

@main.route('/voicemail', methods=['POST'])
def incoming_call():
    """Ugh... someone wants to leave a voicemail..."""
    resp = twiml.Response()

    # Get our mailbox (if it's configured)
    mailbox = Mailbox.query.filter_by(phone_number=request.form['ForwardedFrom']).first()

    # Check if this call was forwarded from our main phone or was direct
    # to our Twilio number
    if 'ForwardedFrom' in request.form:

        if mailbox is None or not mailbox.email:
            # This mailbox doesn't exist / isn't configured: end the call
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
            contact_info = "{0} will receive text messages you send to this number. You can email them at {1}".format(mailbox.name, mailbox.email)
            resp.say(contact_info)

    # Begrudgingly let them leave a voicemail
    resp.say('You may now leave a message after the beep.')

    # Record and transcribe their message
    resp.record(action=url_for('main.hang_up'), transcribe=True,
                transcribeCallback=url_for('main.send_notification'))

    return str(resp)

@main.route('/hang-up', methods=['POST'])
def hang_up():
    """
    Ends a call.
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
def incoming_sms():
    """Receives an SMS message from a number"""
    resp = twiml.Response()
    from_number = request.form['From']

    # If the message has an image, assume this is a user trying to restore
    # their settings
    media_url = request.form.get('MediaUrl0')
    if media_url is not None:
        result = Mailbox.import_config_image(media_url)
        resp.message(result)
        return str(resp)

    # See if we have a Mailbox for this number
    mailbox = Mailbox.query.filter_by(phone_number=from_number).first()

    if mailbox is None:
        # Make sure we don't have another mailbox already
        if Mailbox.query.count() > 0:
            # We're single-tenant for now, so don't make any more mailboxes
            # and ignore the text
            return ('', 204)

        # Make a mailbox for this number
        new_mailbox = Mailbox(from_number)
        db.session.add(new_mailbox)

        # Ask the user for their name
        resp.message(render_template('setup/ask_name.txt'))

    elif not mailbox.name:
        # If we have a mailbox but don't have a name, assume this message
        # contains the user's name
        mailbox.name = request.form['Body']
        db.session.add(mailbox)

        # Ask the user for their email address
        resp.message(render_template('setup/ask_email.txt', mailbox=mailbox))

    elif not mailbox.email:
        # If we have a name but not an email adddress, assume this message
        # contains the user's email address
        form = EmailForm(email=request.form['Body'], csrf_enabled=False)

        if form.validate():
            mailbox.email = request.form['Body']
            db.session.add(mailbox)

            # Tell the user how to set up conditional call forwarding
            resp.message(render_template('setup/call_forwarding.txt', mailbox=mailbox))
        else:
            resp.message(render_template('setup/email_retry.txt'))

    elif not mailbox.call_forwarding_set:
        # Remind the user how to set up call forwarding
        resp.message(render_template('setup/call_forwarding_retry.txt', mailbox=mailbox))

    else:
        # We have no idea why the user is texting us and would prefer it if
        # they left us alone
        resp.message(render_template('setup/no_idea.txt', mailbox=mailbox))

    return str(resp)

@main.route('/config-image')
def config_image():
    """Returns the QR Code for the mailbox"""
    # Get our mailbox
    mailbox = Mailbox.query.first_or_404()
    mailbox_data = mailbox.generate_config_image()

    # Set up a stream
    img_io = BytesIO()
    mailbox_data.save(img_io)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

@main.route('/voice-error', methods=['POST'])
def voice_error():
    """
    Used for our Twilio number's voice fallback URL. Provides a nicer error
    message when something goes wrong on a call
    """
    resp = twiml.Response()
    resp.say(render_template('voice_error.txt'))
    return str(resp)

@main.route('/sms-error', methods=['POST'])
def sms_error():
    """
    Used for our Twilio number's SMS fallback URL. Provides a nicer error
    message when something goes wrong when processing a text message
    """
    resp = twiml.Response()
    resp.message(render_template('sms_error.txt'))
    return str(resp)
