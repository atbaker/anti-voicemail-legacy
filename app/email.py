from flask import current_app, render_template
from flask.ext.mail import Message
from threading import Thread

from . import mail
from .utils import convert_to_national_format


def send_async_email(app, message):
    with app.app_context():
        mail.send(message)

def send_email(voicemail):
    """Send an email about a new voicemail"""
    # Get the current app
    # Note to self: Not sure why I need this...
    app = current_app._get_current_object()

    # Prepare the email message
    subject = 'New voicemail from {0}'.format(
        convert_to_national_format(voicemail.from_number))

    message = Message(subject,
                      sender=app.config['MAIL_SENDER'],
                      recipients=[app.config['MAIL_USERNAME']])
    message.body = render_template('notifications/new_voicemail.txt', voicemail=voicemail)
    message.html = render_template('notifications/new_voicemail.html', voicemail=voicemail)

    # Send it asynchronously
    thread = Thread(target=send_async_email, args=[app, message])
    thread.start()

    return
