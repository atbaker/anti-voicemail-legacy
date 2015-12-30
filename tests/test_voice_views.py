import unittest
from flask import current_app
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.models import Mailbox, Voicemail


class VoiceViewsTestCase(unittest.TestCase):
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

    def test_call_from_mobile(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless',
            name='Jane Foo',
            email='jane@foo.com')
        db.session.add(mailbox)

        mock_lookup_result = MagicMock(carrier={'type': 'mobile', 'name': 'Foo Wireless'})

        # Act
        with patch('app.voice.views.look_up_number', return_value=mock_lookup_result):
            with patch.object(Mailbox, 'send_contact_info') as mock:
                response = self.test_client.post('/call', data={
                    'From': '+17777777777'
                    })

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('Jane Foo', content)
        self.assertIn('I am sending you a text message', content)

        mock.assert_called_once_with('+17777777777')

    def test_call_from_mobile_retry(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless',
            name='Jane Foo',
            email='jane@foo.com')
        db.session.add(mailbox)

        mock_lookup_result = MagicMock(carrier={'type': 'mobile', 'name': 'Foo Wireless'})

        # Act
        with patch('app.voice.views.look_up_number', return_value=mock_lookup_result):
            with patch.object(Mailbox, 'send_contact_info') as mock:
                response = self.test_client.post('/error', data={
                    'From': '+17777777777',
                    'ErrorCode': '11200',
                    'ErrorUrl': '/call'
                    })

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('Jane Foo', content)
        self.assertIn('I am sending you a text message', content)

        self.assertFalse(mock.called)

    def test_call_from_non_mobile(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless',
            name='Jane Foo',
            email='jane@foo.com')
        db.session.add(mailbox)

        mock_lookup_result = MagicMock(carrier={'type': 'landline', 'name': 'Cromcrast'})

        # Act
        with patch('app.voice.views.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/call', data={
                'From': '+17777777777'
                })

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('Jane Foo', content)
        self.assertNotIn('I am sending you a text message', content)
        self.assertIn('jane@foo.com', content)
        self.assertIn('<Gather', content)
        self.assertIn('press 1', content)

    def test_call_redirect_to_record(self):
        # Arrange
        self.app.cache.set('+17777777777', True)

        # Act
        response = self.test_client.post('/call', data={'From': '+17777777777'})

        # Assert
        self.assertEqual(response.status_code, 302)

        content = str(response.data)
        self.assertIn('/record', content)

    def test_call_caller_in_whitelist(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless',
            name='Jane Foo',
            email='jane@foo.com',
            whitelist=['+17777777777'])
        db.session.add(mailbox)

        # Act
        response = self.test_client.post('/call', data={
            'From': '+17777777777'})

        # Assert
        self.assertEqual(response.status_code, 302)

        content = str(response.data)
        self.assertIn('/record', content)

    def test_call_no_mailbox(self):
        # Act
        response = self.test_client.post('/call', data={
            'From': '+17777777777'
            })

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('cannot receive voicemails right now.', content)

    def test_record_no_digits(self):
        # Act
        response = self.test_client.get('/record')

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('leave a message', content)
        self.assertIn('<Record action="/hang-up" transcribe="true" transcribeCallback="/send-notification" />', content)

    def test_record_pressed_one(self):
        # Act
        response = self.test_client.get('/record', data={'Digits': '1'})

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('leave a message', content)
        self.assertIn('<Record action="/hang-up" transcribe="true" transcribeCallback="/send-notification" />', content)

    def test_record_did_not_press_one(self):
        # Act
        response = self.test_client.get('/record', data={'Digits': '5'})

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('Thank you for not leaving a voicemail.', content)

    def test_hang_up(self):
        # Act
        response = self.test_client.post('/hang-up')

        # Assert
        self.assertEqual(response.status_code, 200)
        content = str(response.data)

        self.assertIn('recorded. Goodbye', content)

    def test_send_notification(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        with patch.object(Voicemail, 'send_notification') as mock_method:
            response = self.test_client.post('/send-notification', data={
                'From': '+17777777777',
                'TranscriptionText': 'YOUR VOICEMAIL IS COOL!',
                'RecordingSid': '1234'
                })

        # Assert
        self.assertEqual(response.status_code, 204)

        mock_method.assert_called_once_with()

    def test_view_recording(self):
        # Arrange
        mock_recording = MagicMock()
        mock_recording.call_sid = '5678'

        mock_call = MagicMock()
        mock_call.from_ = '+15555555555'

        mock_client = MagicMock()
        mock_client.recordings.get.return_value = mock_recording
        mock_client.calls.get.return_value = mock_call

        # Act
        with patch('app.voice.views.get_twilio_rest_client', return_value=mock_client):
            response = self.test_client.get('/recording/1234')

        # Assert
        self.assertEqual(response.status_code, 200)
        mock_client.recordings.get.assert_called_once_with('1234')
