#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Mailbox, Voicemail
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Mailbox=Mailbox, Voicemail=Voicemail)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import sys, unittest
    tests = unittest.TestLoader().discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)

    if not result.wasSuccessful():
        sys.exit(1)


@manager.command
def reset():
    """Deletes all data from the database"""
    Mailbox.query.delete()
    print("Mailbox deleted")

if __name__ == '__main__':
    manager.run()
