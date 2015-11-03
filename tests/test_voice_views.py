import unittest
from flask import current_app
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.models import Mailbox, Voicemail
from app.utils import look_up_number, set_twilio_number_urls


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
        db.session.commit()

        mock_lookup_result = MagicMock(carrier={'type': 'mobile', 'name': 'Foo Wireless'})

        # Act
        with patch('app.voice.views.look_up_number', return_value=mock_lookup_result):
            with patch.object(Mailbox, 'send_contact_info') as mock_method:
                response = self.test_client.post('/call', data={
                    'ForwardedFrom': '+15555555555',
                    'From': '+17777777777'
                    })

        # Assert
        content = str(response.data)

        self.assertIn('Jane Foo', content)
        self.assertIn('I am sending you a text message', content)

        mock_method.assert_called_once_with('+17777777777')

    def test_call_from_non_mobile(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless',
            name='Jane Foo',
            email='jane@foo.com')
        db.session.add(mailbox)
        db.session.commit()

        mock_lookup_result = MagicMock(carrier={'type': 'landline', 'name': 'Cromcrast'})

        # Act
        with patch('app.voice.views.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/call', data={
                'ForwardedFrom': '+15555555555',
                'From': '+17777777777'
                })

        # Assert
        content = str(response.data)

        self.assertIn('Jane Foo', content)
        self.assertNotIn('I am sending you a text message', content)
        self.assertIn('jane@foo.com', content)
        self.assertIn('<Gather', content)
        self.assertIn('press 1', content)

    def test_call_redirect_to_record(self):
        # Act
        response = self.test_client.post('/call', data={'From': '+17777777777'})

        # Assert
        content = str(response.data)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/record', content)

    def test_call_no_mailbox(self):
        # Act
        response = self.test_client.post('/call', data={
            'ForwardedFrom': '+15555555555',
            'From': '+17777777777'
            })

        # Assert
        content = str(response.data)

        self.assertIn('cannot receive voicemails right now.', content)

    def test_record_no_digits(self):
        # Act
        response = self.test_client.get('/record')

        # Assert
        content = str(response.data)

        self.assertIn('leave a message', content)
        self.assertIn('<Record action="/hang-up" transcribe="true" transcribeCallback="/send-notification" />', content)

    def test_record_pressed_one(self):
        # Act
        response = self.test_client.get('/record', data={'Digits': '1'})

        # Assert
        content = str(response.data)

        self.assertIn('leave a message', content)
        self.assertIn('<Record action="/hang-up" transcribe="true" transcribeCallback="/send-notification" />', content)

    def test_record_did_not_press_one(self):
        # Act
        response = self.test_client.get('/record', data={'Digits': '5'})

        # Assert
        content = str(response.data)

        self.assertIn('Thank you for not leaving a voicemail.', content)

    def test_hang_up(self):
        # Act
        response = self.test_client.post('/hang-up')

        # Assert
        content = str(response.data)

        self.assertIn('recorded. Goodbye', content)

    def test_send_notification(self):
        # Arrange
        mailbox = Mailbox(
            phone_number='+15555555555',
            carrier='Foo Wireless')
        db.session.add(mailbox)
        db.session.commit()

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
        mock_client = MagicMock()

        # Act
        with patch('app.voice.views.get_twilio_rest_client', return_value=mock_client):
            response = self.test_client.get('/recording/1234')

        # Assert
        self.assertEqual(response.status_code, 200)
        mock_client.recordings.get.assert_called_once_with('1234')

    # def test_look_up_number(self):
    #     # Arrange
    #     mock_client = MagicMock()
    #     mock_client.phone_numbers.get.return_value = 'lookup info'

    #     # Act
    #     with patch('app.utils.TwilioLookupsClient', return_value=mock_client):
    #         result = look_up_number('+15555555555')

    #     # Assert
    #     self.assertEqual(result, 'lookup info')
    #     mock_client.phone_numbers.get.assert_called_once_with('+15555555555', include_carrier_info=True)

    # def test_set_twilio_urls_all(self):
    #     # Arrange
    #     mock_number = MagicMock()
    #     mock_number.voice_url = None
    #     mock_number.sms_url = None
    #     mock_number.voice_fallback_url = None
    #     mock_number.sms_fallback_url = None

    #     mock_client = MagicMock()
    #     mock_client.phone_numbers.list.return_value = [mock_number]

    #     # Act
    #     with patch('app.utils.TwilioRestClient', return_value=mock_client):
    #         set_twilio_number_urls()

    #     # Assert
    #     mock_number.update.assert_called_once_with(
    #         voice_url='http://localhost/call',
    #         sms_url='http://localhost/sms',
    #         voice_fallback_url='http://localhost/voice-error',
    #         sms_fallback_url='http://localhost/sms-error')

    # def test_set_twilio_urls_none(self):
    #     # Arrange
    #     mock_number = MagicMock()
    #     mock_number.voice_url = 'http://example.com/call'
    #     mock_number.sms_url = 'http://example.com/sms'
    #     mock_number.voice_fallback_url = 'http://example.com/voice-error'
    #     mock_number.sms_fallback_url = 'http://example.com/sms-error'

    #     mock_client = MagicMock()
    #     mock_client.phone_numbers.list.return_value = [mock_number]

    #     # Act
    #     with patch('app.utils.TwilioRestClient', return_value=mock_client):
    #         set_twilio_number_urls()

    #     # Assert
    #     self.assertFalse(mock_number.update.called)



    # # def test_mailbox_init(self):
    # #     # Arrange
    # #     mock_lookup_result = MagicMock()
    # #     mock_lookup_result.carrier = {'name': 'Foo Wireless'}

    # #     # Act
    # #     with patch('app.models.lookup_number', return_value=mock_lookup_result):
    # #         mailbox = Mailbox('+15555555555')

    # #     # Assert
    # #     self.assertEqual(str(mailbox), "<Mailbox '+15555555555'>")
    # #     self.assertEqual(mailbox.carrier, 'Foo Wireless')
