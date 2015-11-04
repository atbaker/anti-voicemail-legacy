import unittest
from flask import current_app
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.models import Mailbox, Voicemail


class MailboxTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_mailbox_init(self):
        # Arrange
        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Foo Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            mailbox = Mailbox('+15555555555')

        # Assert
        self.assertEqual(str(mailbox), "<Mailbox '+15555555555'>")
        self.assertEqual(mailbox.carrier, 'Foo Wireless')

    def test_get_call_forwarding_code(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Verizon Wireless')

        # Act
        forwarding_code = mailbox.get_call_forwarding_code()

        # Assert
        self.assertEqual(forwarding_code, '*719999999999')

    def test_get_disable_code(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Verizon Wireless')

        # Act
        disable_code = mailbox.get_disable_code()

        # Assert
        self.assertEqual(disable_code, '*73')

    def test_send_contact_info(self):
        # Arrange
        mailbox = Mailbox('+15555555555', name='Jane Foo', email='jane@foo.com', carrier='Foo Wireless')
        mock_client = MagicMock()

        # Act
        with patch('app.models.get_twilio_rest_client', return_value=mock_client):
            mailbox.send_contact_info('+17777777777')

        # Assert
        assert mock_client.messages.create.called
        self.assertFalse(mailbox.call_forwarding_set)

    def test_send_info_to_user(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless')
        mock_client = MagicMock()

        mock_thread = MagicMock()

        # Act
        with patch('app.models.get_twilio_rest_client', return_value=mock_client):
            with patch('app.models.Thread', return_value=mock_thread) as MockThread:
                mailbox.send_contact_info('+15555555555')

        # Assert
        assert mock_client.messages.create.called
        self.assertTrue(mailbox.call_forwarding_set)

        body = MockThread.call_args[1]['args'][1]
        self.assertIn('do you like QR codes?', body)

        assert mock_thread.start.called

    def test_send_info_to_user_restore(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless', feelings_on_qr_codes='love')
        mock_client = MagicMock()

        mock_thread = MagicMock()

        # Act
        with patch('app.models.get_twilio_rest_client', return_value=mock_client):
            with patch('app.models.Thread', return_value=mock_thread) as MockThread:
                mailbox.send_contact_info('+15555555555')

        # Assert
        assert mock_client.messages.create.called
        self.assertTrue(mailbox.call_forwarding_set)

        body = MockThread.call_args[1]['args'][1]
        self.assertIn('Now get on with your life!', body)

        assert mock_thread.start.called

    def test_generate_config_image(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless')

        # Act
        with patch('app.models.qrcode') as mock_qrcode:
            mailbox.generate_config_image()

        # Assert
        assert mock_qrcode.make.called

        qrcode_json = mock_qrcode.make.call_args[0][0]
        self.assertIn('+1555555555', qrcode_json)
        self.assertIn('"call_forwarding_set": false', qrcode_json)
        self.assertNotIn('_sa_instance_state', qrcode_json)

    def test_send_config_image(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless')
        mock_client = MagicMock()

        # Act
        with patch('app.models.get_twilio_rest_client', return_value=mock_client):
            mailbox.send_config_image()

        # Assert
        assert mock_client.messages.create.called

        args = mock_client.messages.create.call_args[1]
        self.assertEqual(args['media_url'], 'http://localhost/config-image')

    def test_import_config_image(self):
        # Arrange
        # Start off with an existing Mailbox
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless', call_forwarding_set=True)
        db.session.add(mailbox)
        db.session.commit()

        mock_response = MagicMock()
        mock_response.json.return_value = [{'type': 'qrcode', 'symbol': [{'data': '{"id": 1, "feelings_on_qr_codes": "like", "phone_number": "+15555555555", "name": "Jane Foo", "email": "jane@foo.com", "call_forwarding_set": false, "carrier": "Foo Wireless"}', 'error': None, 'seq': 0}]}]

        # Act
        with patch('app.models.requests.get', return_value=mock_response):
            result = Mailbox.import_config_image('http://example.com')

        # Assert
        self.assertEqual(Mailbox.query.count(), 1)

        imported_mailbox = Mailbox.query.one()
        self.assertEqual(mailbox.phone_number, '+15555555555')
        self.assertFalse(mailbox.call_forwarding_set)

        self.assertIn('Now I remember *everything* about you', result)

    def test_import_config_image_failure(self):
        # Arrange
        mock_response = MagicMock()

        mock_response.json.side_effect = ValueError
        
        # Act
        with patch('app.models.requests.get', return_value=mock_response):
            result = Mailbox.import_config_image('http://example.com')

        # Assert
        self.assertIn('Ooops!', result)

class VoicemailTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_voicemail_init(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        voicemail = Voicemail('+17777777777', 'transcription', '12345')

        # Assert
        self.assertEqual(voicemail.mailbox, mailbox)

    def test_send_notification(self):
        # Arrange
        mailbox = Mailbox('+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)
        db.session.commit()

        voicemail = Voicemail('+17777777777', 'hello world', '12345')
        mock_client = MagicMock()

        # Act
        with patch('app.models.get_twilio_rest_client', return_value=mock_client):
            voicemail.send_notification()

        # Assert
        assert mock_client.messages.create.called

        body = mock_client.messages.create.call_args[1]['body']
        self.assertIn('(777) 777-7777', body)
        self.assertIn('hello world', body)
        self.assertIn('http://localhost/recording/12345', body)
