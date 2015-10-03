import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # User config values
    PHONE_NUMBER = os.environ.get('PHONE_NUMBER')
    TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')

    # Twilio credentials
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    # Flask-Mail
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = 'Anti-voicemail <no-reply@antivoicemail.com>'

    # Determine which notification types have been configured
    SMS_NOTIFICATIONS = TWILIO_PHONE_NUMBER is not None
    EMAIL_NOTIFICATIONS = MAIL_USERNAME is not None

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
