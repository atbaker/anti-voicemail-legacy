from flask import abort, current_app, render_template, request, send_file
from io import BytesIO
from twilio import twiml

from . import setup
from .forms import EmailForm, PhoneNumberForm
from ..voice.views import incoming_call
from .. import db
from ..decorators import validate_twilio_request
from ..models import Mailbox
from ..utils import set_twilio_number_urls


@setup.route('/')
def index():
    # While we're rendering the homepage, do the user a favor and configure
    # their Twilio phone number callback URLs for them (if they haven't
    # already)
    set_twilio_number_urls()

    return render_template('index.html', twilio_number=current_app.config[
                           'TWILIO_PHONE_NUMBER'])


@setup.route('/message', methods=['POST'])
@validate_twilio_request
def incoming_message():
    """Receives an SMS message from a number"""
    resp = twiml.Response()

    # If this message has an image attached, attempt to import it
    if 'MediaUrl0' in request.form:
        reply = _import_config(request.form['From'], request.form['MediaUrl0'])
        resp.message(reply)
        return str(resp)

    # See if we have a Mailbox for this number
    from_number = request.form['From']
    mailbox = Mailbox.query.filter_by(phone_number=from_number).first()

    if mailbox is None:
        # Make sure we don't have another mailbox already
        if Mailbox.query.count() > 0:
            # We're single-tenant for now, so don't make any more mailboxes
            # and ignore the text
            return ('', 204)

        # Make a mailbox for this number
        new_mailbox = Mailbox(from_number)

        # Check that our new user's carrier is supported by Anti-Voicemail
        if new_mailbox.is_carrier_supported():
            db.session.add(new_mailbox)

            # Ask the user for their name
            reply = render_template('setup/ask_name.txt')
        else:
            # Their carrier is unsupported. Bummer!
            reply = render_template('setup/unsupported_carrier.txt')

        resp.message(reply)

    else:
        # Check if this answer is one of our special commands
        body = request.form['Body'].split()
        command = body[0].lower()

        if command in current_app.config['ANTI_VOICEMAIL_COMMANDS']:
            reply = _process_command(command, body, mailbox, from_number)
        else:
            # Assume this message is an answer to a setup question and process
            # it accordingly
            reply = _process_answer(request.form['Body'], mailbox)

        resp.message(reply)

    return str(resp)


def _import_config(from_number, image_url):
    """Processes a config image that the user has sent us"""
    # First see if we have an existing mailbox
    mailbox = Mailbox.query.first()

    # If we *do* have an existing mailbox, ignore the upload
    # unless it's from the same phone_number (to prevent abuse)
    if mailbox is not None and mailbox.phone_number != from_number:
        abort(403)

    # Otherwise, attempt to import the config image
    result = Mailbox.import_config_image(image_url)

    return result


def _process_command(command, body, mailbox, from_number):
    """A helper function to process commands sent from the user"""
    if command == 'disable':
        # Send the instructions to disable Anti-Voicemail
        reply = render_template('setup/disable.txt', mailbox=mailbox)
    elif command == 'whitelist':
        # Make sure the phone number is valid
        phone_number = ' '.join(body[1:])
        form = PhoneNumberForm(phone_number=phone_number,
                               default_region_code=mailbox.get_region_code())

        if form.validate():
            whitelisted_number = form.phone_number.data

            # We need to make a new whitelist object to ensure the
            # PickleType field detects a change
            mailbox.whitelist = mailbox.whitelist.union(
                set([whitelisted_number]))
            db.session.add(mailbox)

            reply = render_template('setup/whitelist/success.txt',
                                    new_number=whitelisted_number,
                                    whitelist=list(mailbox.whitelist))
        else:
            reply = render_template('setup/whitelist/retry.txt')
    elif command == 'reset':
        # Delete the existing Mailbox and begin the setup process again
        Mailbox.query.delete()

        new_mailbox = Mailbox(from_number)
        db.session.add(new_mailbox)

        reply = render_template('setup/ask_name.txt', reset=True)
    else:
        # The only way this happens is if there's a mismatch between
        # the ANTI_VOICEMAIL_COMMANDS config setting and this method
        reply = """Ooops! There's a mismatch between your
                ANTI_VOICEMAIL_COMMANDS config setting and your
                _process_command function. Better check that!"""

    return reply


def _process_answer(answer, mailbox):
    """A helper function to process answers to the setup questions"""
    reply = None

    if not mailbox.name:
        # If we have a mailbox but don't have a name, assume this message
        # contains the user's name
        mailbox.name = answer
        db.session.add(mailbox)

        # Ask the user for their email address
        reply = render_template('setup/email/ask.txt', mailbox=mailbox)

    elif not mailbox.email:
        # If we have a name but not an email adddress, assume this message
        # contains the user's email address
        form = EmailForm(email=answer, csrf_enabled=False)

        if form.validate():
            mailbox.email = answer
            db.session.add(mailbox)

            # Tell the user how to set up conditional call forwarding
            reply = render_template(
                'setup/call_forwarding/instructions.txt',
                mailbox=mailbox)
        else:
            reply = render_template('setup/email/retry.txt')

    elif not mailbox.call_forwarding_set:
        # Remind the user how to set up call forwarding
        reply = render_template(
            'setup/call_forwarding/retry.txt',
            mailbox=mailbox)

    elif not mailbox.feelings_on_qr_codes:
        # Most input will probably be something like yes/yeah/yea or
        #  no/nope/naw so we'll try taking the first character
        answer = answer[0].lower()

        if answer == 'y':
            mailbox.feelings_on_qr_codes = 'love'
            db.session.add(mailbox)
            reply = render_template('setup/qr_codes/loves.txt')

            # Our user likes QR codes, so we'll send them the config image
            mailbox.send_config_image()
        elif answer == 'n':
            mailbox.feelings_on_qr_codes = 'hate'
            db.session.add(mailbox)
            reply = render_template('setup/qr_codes/hates.txt')
        else:
            reply = render_template('setup/qr_codes/retry.txt')

    else:
        # We have no idea why the user is texting us and would prefer it if
        # they left us alone
        reply = render_template('setup/no_idea.txt')

    return reply


@setup.route('/config-image')
def config_image():
    """Returns the QR Code for the mailbox"""
    # Get our mailbox and its config image
    mailbox = Mailbox.query.first_or_404()
    mailbox_data = mailbox.generate_config_image()

    # Set up a stream
    img_io = BytesIO()
    mailbox_data.save(img_io)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@setup.route('/error', methods=['POST'])
def handle_error():
    """
    Handles errors for incoming messages. Twilio will POST to this view
    when it encounters an error in its request to /message.

    Unlike the voice app handle_error method, it doesn't attempt to retry any
    requests
    """
    # If an 'ErrorCode' field is not in the data, then this request didn't
    # originate from an error
    error_code = request.form.get('ErrorCode')
    if error_code is None:
        return ('', 400)

    # If the ErrorCode is a HTTP retrieval error, retry the original view
    voice_error = '/call' in request.form['ErrorUrl']
    if error_code == '11200':
        try:
            if voice_error:
                return incoming_call(retry=True)
            else:
                return incoming_message()
        except Exception:
            # It failed again, so this is a real error and we should apologize
            # to the caller
            pass

    resp = twiml.Response()
    if voice_error:
        resp.say(render_template('voice/error.txt'), voice='alice')
    else:
        resp.message(render_template('setup/error.txt'))

    return str(resp)
