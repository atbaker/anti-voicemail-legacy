from flask import current_app, render_template
from flask.ext.mail import Message
from . import mail


# def send_email(to, subject, template, **kwargs):
def send_email(voicemail):
    """Send an email about a new voicemail"""
    # Get the current app
    # Note to self: Not sure why I need this...
    app = current_app._get_current_object()

    # Prepare the email message
    subject = 'New voicemail from {0} at {1}'.format(
        voicemail.get_national_format(), voicemail.get_local_time())

    message = Message(subject,
                      sender=app.config['MAIL_SENDER'],
                      recipients=[app.config['MAIL_USERNAME']])
    message.body = render_template('notifications/new_voicemail.txt', voicemail=voicemail)
    message.html = render_template('notifications/new_voicemail.html', voicemail=voicemail)

    # Send it
    mail.send(message)

    return