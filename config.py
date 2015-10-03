import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask-Mail
    MAIL_SERVER = 'smtp.googlemail.com'
    FLASKY_MAIL_SENDER = 'Anti-voicemail <no-reply@antivoicemail.com>'

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
