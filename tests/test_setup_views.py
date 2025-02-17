import unittest
from flask import current_app
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.models import Mailbox, Voicemail
from app.setup.views import _import_config, _process_command, _process_answer


class SMSViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        self.test_client = self.app.test_client()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index(self):
        # Act
        with patch('app.setup.views.set_twilio_number_urls') as mock:
            response = self.test_client.get('/')

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with()

    def test_sms_no_mailbox_good_carrier(self):
        # Arrange
        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Verizon Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/message', data={'From': '+15555555555'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mailbox = Mailbox.query.one()
        self.assertEqual(mailbox.phone_number, '+15555555555')

        content = str(response.data)
        self.assertIn("your name", content)

    def test_sms_no_mailbox_bad_carrier(self):
        # Arrange
        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Foo Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/message', data={'From': '+15555555555'})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Mailbox.query.count(), 0)

        content = str(response.data)
        self.assertIn("support that carrier", content)

    def test_sms_no_second_mailbox(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        response = self.test_client.post('/message', data={'From': '+16666666666'})

        # Assert
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Mailbox.query.count(), 1)

    def test_sms_config_image(self):
        # Act
        with patch('app.setup.views._import_config', return_value='Image processed!') as mock:
            response = self.test_client.post('/message', data={
                'From': '+15555555555',
                'MediaUrl0': 'http://i.imgur.com/VMSuO1N.gif'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with('+15555555555', 'http://i.imgur.com/VMSuO1N.gif')

        content = str(response.data)
        self.assertIn('Image processed!', content)

    def test_sms_process_command(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        with patch('app.setup.views._process_command', return_value='Command processed!') as mock:
            response = self.test_client.post('/message', data={
                'From': '+15555555555',
                'Body': 'reset'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with('reset', ['reset'], mailbox, '+15555555555')

        content = str(response.data)
        self.assertIn('Command processed!', content)

    def test_sms_process_answer(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        with patch('app.setup.views._process_answer', return_value='Answer processed!') as mock:
            response = self.test_client.post('/message', data={
                'From': '+15555555555',
                'Body': 'Jane Foo'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with('Jane Foo', mailbox)

        content = str(response.data)
        self.assertIn('Answer processed!', content)

class ImportConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_import_config_no_mailbox(self):
        # Act
        with patch('app.setup.views.Mailbox.import_config_image', return_value='Imported!') as mock:
            result = _import_config('+15555555555', 'http://i.imgur.com/VMSuO1N.gif')

        # Assert
        self.assertEqual(result, 'Imported!')
        mock.assert_called_once_with('http://i.imgur.com/VMSuO1N.gif')

    def test_import_config_same_number(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)
        db.session.commit()

        # Act
        with patch('app.setup.views.Mailbox.import_config_image', return_value='Imported!') as mock:
            result = _import_config('+15555555555', 'http://i.imgur.com/VMSuO1N.gif')

        # Assert
        self.assertEqual(result, 'Imported!')
        mock.assert_called_once_with('http://i.imgur.com/VMSuO1N.gif')

    def test_import_config_diff_number(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)
        db.session.commit()

        # Act
        with patch('app.setup.views.Mailbox.import_config_image') as mock:
            from werkzeug.exceptions import Forbidden
            with self.assertRaises(Forbidden):
                _import_config('+17777777777', 'http://i.imgur.com/VMSuO1N.gif')

        # Assert
        self.assertFalse(mock.called)

class ProcessCommandTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_disable(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Verizon Wireless')

        # Act
        reply = _process_command('disable', ['disable'], mailbox, '+15555555555')

        # Assert
        self.assertIn('*73', reply)

    def test_sms_whitelist(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')

        # Act
        body = 'whitelist 415 777 7777'
        reply = _process_command('whitelist', body.split(), mailbox, '+15555555555')

        # Assert
        self.assertEqual(mailbox.whitelist, set(['+14157777777']))
        self.assertIn('always allow calls from (415) 777-7777', reply)

    def test_sms_whitelist_bad_number(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')

        # Act
        body = 'whitelist 415 777'
        reply = _process_command('whitelist', body.split(), mailbox, '+15555555555')

        # Assert
        self.assertEqual(mailbox.whitelist, set())
        self.assertIn('an you send it to me again?', reply)

    def test_sms_reset_command(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Bar Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            reply = _process_command('reset', ['reset'], mailbox, '+15555555555')

        # Assert
        self.assertIn('Bzzzzt!', reply)

        mailboxes = Mailbox.query.all()
        self.assertEqual(len(mailboxes), 1)
        self.assertEqual(mailboxes[0].carrier, 'Bar Wireless')

    def test_unknown_command(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')

        # Act
        reply = _process_command('halp', ['halp'], mailbox, '+15555555555')

        # Assert
        self.assertIn('ANTI_VOICEMAIL_COMMANDS', reply)

class ProcessAnswerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_name(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')

        # Act
        reply = _process_answer('Jane Foo', mailbox)

        # Assert
        self.assertEqual(mailbox.name, 'Jane Foo')
        self.assertIn('your email address', reply)

    def test_email(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo')

        # Act
        reply = _process_answer('jane@foo.com', mailbox)

        # Assert
        self.assertEqual(mailbox.email, 'jane@foo.com')
        self.assertIn('forward your missed calls', reply)

    def test_invalid_email(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo')

        # Act
        reply = _process_answer('jane@foo', mailbox)

        # Assert
        self.assertIsNone(mailbox.email)
        self.assertIn('Maybe it has a typo', reply)

    def test_call_forwarding_reminder(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo',
            email='jane@foo.com')

        # Act
        reply = _process_answer('halp', mailbox)

        # Assert
        self.assertIn('still waiting to receive my first voicemail', reply)

    def test_qr_codes_yes(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo',
            email='jane@foo.com',
            call_forwarding_set=True)
        mailbox.send_config_image = MagicMock()

        # Act
        reply = _process_answer('YEAH', mailbox)

        # Assert
        self.assertEqual(mailbox.feelings_on_qr_codes, 'love')
        self.assertIn('ME TOO', reply)

        mailbox.send_config_image.assert_called_once_with()

    def test_qr_codes_no(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo',
            email='jane@foo.com',
            call_forwarding_set=True)
        mailbox.send_config_image = MagicMock()

        # Act
        reply = _process_answer('not so much', mailbox)

        # Assert
        self.assertEqual(mailbox.feelings_on_qr_codes, 'hate')
        self.assertIn('for nerds', reply)

        self.assertFalse(mailbox.send_config_image.called)

    def test_qr_codes_unsure(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo',
            email='jane@foo.com',
            call_forwarding_set=True)
        mailbox.send_config_image = MagicMock()

        # Act
        reply = _process_answer("I can take them or leave them", mailbox)

        # Assert
        self.assertIsNone(mailbox.feelings_on_qr_codes)
        self.assertIn('kidder', reply)

        self.assertFalse(mailbox.send_config_image.called)

    def test_no_idea(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Verizon Wireless',
            name='Jane Foo',
            email='jane@foo.com',
            call_forwarding_set=True,
            feelings_on_qr_codes='love')

        # Act
        reply = _process_answer("I'm the user and I feel lonely!", mailbox)

        # Assert
        self.assertIn('Looking for help?', reply)

class ConfigImageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        self.test_client = self.app.test_client()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_config_image(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        response = self.test_client.get('/config-image')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'image/png')
        self.assertTrue(response.is_streamed)


class ErrorHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

        self.app_context = self.app.app_context()
        self.app_context.push()

        self.test_client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_handle_error_no_error_code(self):
        # Act
        response = self.test_client.post('/error', data={})

        # Assert
        self.assertEqual(response.status_code, 400)

    def test_voice_error_retry_success(self):
        # Act
        with patch('app.setup.views.incoming_call', return_value='foo') as mock:
            response = self.test_client.post('/error', data={
                'ErrorCode': '11200',
                'ErrorUrl': '/call'
                })

        # Assert
        mock.assert_called_once_with(retry=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('foo', str(response.data))

    def test_voice_error_retry_fail(self):
        # Arrange
        mock = MagicMock(side_effect=Exception())

        # Act
        with patch('app.setup.views.incoming_call', mock):
            response = self.test_client.post('/error', data={
                'ErrorCode': '11200',
                'ErrorUrl': '/call'
                })

        # Assert
        mock.assert_called_once_with(retry=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('If this number belongs to you', str(response.data))

    def test_message_error_retry_success(self):
        # Act
        with patch('app.setup.views.incoming_message', return_value='foo') as mock:
            response = self.test_client.post('/error', data={
                'ErrorCode': '11200',
                'ErrorUrl': '/message'
                })

        # Assert
        mock.assert_called_once_with()

        self.assertEqual(response.status_code, 200)
        self.assertIn('foo', str(response.data))

    def test_message_error_retry_fail(self):
        # Arrange
        mock = MagicMock(side_effect=Exception())

        # Act
        with patch('app.setup.views.incoming_message', mock):
            response = self.test_client.post('/error', data={
                'ErrorCode': '11200',
                'ErrorUrl': '/message'
                })

        # Assert
        mock.assert_called_once_with()

        self.assertEqual(response.status_code, 200)
        self.assertIn('Oh dear', str(response.data))

    def test_handle_error_no_retry(self):
        # Act
        response = self.test_client.post('/error', data={
            'ErrorCode': 'fooo',
            'ErrorUrl': '/call'
            })

        # Assert
        self.assertEqual(response.status_code, 200)
