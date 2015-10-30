from flask import current_app, send_file, render_template, request
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
