from flask import current_app, redirect, render_template, request, send_file, url_for
from io import BytesIO
from twilio import twiml

from . import setup
from .forms import EmailForm
from .. import db
from ..models import Mailbox
from ..utils import set_twilio_number_urls


@setup.route('/')
def index():
    # While we're rendering the homepage, do the user a favor and configure
    # their Twilio phone number callback URLs for them (if they haven't already)
    set_twilio_number_urls()

    return render_template('index.html', twilio_number=current_app.config['TWILIO_PHONE_NUMBER'])

@setup.route('/sms', methods=['POST'])
def incoming_sms():
    """Receives an SMS message from a number"""
    # Redirect to the import_config view if this message has an image attached
    if 'MediaUrl0' in request.form:
        return redirect(url_for('setup.import_config'))

    resp = twiml.Response()
    from_number = request.form['From']

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

    else:
        # Check if this answer is one of our special commands
        command = request.form['Body'].lower()
        if command == 'disable':
            # Send the instructions to disable Anti-Voicemail
            resp.message(render_template('setup/disable.txt', mailbox=mailbox))
        elif command == 'reset':
            # Delete the existing Mailbox and begin the setup process again
            Mailbox.query.delete()

            new_mailbox = Mailbox(from_number)
            db.session.add(new_mailbox)

            resp.message(render_template('setup/ask_name.txt', reset=True))
        else:
            # Assume this message is an answer to a setup question and process it
            # accordingly
            reply = _process_answer(mailbox)
            resp.message(reply)

    return str(resp)

def _process_answer(mailbox):
    """A helper function to process answers to the setup questions"""
    reply = None

    if not mailbox.name:
        # If we have a mailbox but don't have a name, assume this message
        # contains the user's name
        mailbox.name = request.form['Body']
        db.session.add(mailbox)

        # Ask the user for their email address
        reply = render_template('setup/ask_email.txt', mailbox=mailbox)

    elif not mailbox.email:
        # If we have a name but not an email adddress, assume this message
        # contains the user's email address
        form = EmailForm(email=request.form['Body'], csrf_enabled=False)

        if form.validate():
            mailbox.email = request.form['Body']
            db.session.add(mailbox)

            # Tell the user how to set up conditional call forwarding
            reply = render_template('setup/call_forwarding.txt', mailbox=mailbox)
        else:
            reply = render_template('setup/retry_email.txt')

    elif not mailbox.call_forwarding_set:
        # Remind the user how to set up call forwarding
        reply = render_template('setup/call_forwarding_retry.txt', mailbox=mailbox)

    elif not mailbox.feelings_on_qr_codes:
        # Most input will probably be something like yes/yeah/yea or no/nope/naw
        # so we'll try taking the first character
        answer = request.form['Body'][0].lower()

        if answer == 'y':
            mailbox.feelings_on_qr_codes = 'like'
            db.session.add(mailbox)
            reply = render_template('setup/likes_qr_codes.txt')

            # Our user likes QR codes, so we'll send them the config image
            mailbox.send_config_image()
        elif answer == 'n':
            mailbox.feelings_on_qr_codes = 'hate'
            db.session.add(mailbox)
            reply = render_template('setup/hates_qr_codes.txt')
        else:
            reply = render_template('setup/retry_qr_codes.txt')

    else:
        # We have no idea why the user is texting us and would prefer it if
        # they left us alone
        reply = render_template('setup/no_idea.txt')

    return reply

@setup.route('/config-image')
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

@setup.route('/import-config', methods=['POST'])
def import_config():
    """Processes a config image that the user has sent us"""
    # First see if we have an existing mailbox
    mailbox = Mailbox.query.first()

    # If we *do* have an existing mailbox, ignore the upload
    # unless it's from the same phone_number (to prevent abuse)
    if mailbox is not None and mailbox.phone_number != request.form['From']:
        return ('', 204)

    # Otherwise, attempt to import the config image
    resp = twiml.Response()

    result = Mailbox.import_config_image(request.form['MediaUrl0'])
    resp.message(result)

    return str(resp)

@setup.route('/voice-error', methods=['POST'])
def voice_error():
    """
    Used for our Twilio number's voice fallback URL. Provides a nicer error
    message when something goes wrong on a call
    """
    resp = twiml.Response()
    resp.say(render_template('voice_error.txt'))
    return str(resp)

@setup.route('/sms-error', methods=['POST'])
def sms_error():
    """
    Used for our Twilio number's SMS fallback URL. Provides a nicer error
    message when something goes wrong when processing a text message
    """
    resp = twiml.Response()
    resp.message(render_template('sms_error.txt'))
    return str(resp)
