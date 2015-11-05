import unittest
from flask import current_app
from twilio.rest.exceptions import TwilioRestException
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.utils import look_up_number, send_async_message, set_twilio_number_urls


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_send_async_message(self):
        # Arrange
        mock_client = MagicMock()

        # Act
        with patch('app.utils.get_twilio_rest_client', return_value=mock_client):
            with patch('app.utils.sleep') as mock_sleep:
                send_async_message(self.app, 'Async foo', '+15555555555')

        # Assert
        mock_sleep.assert_called_once_with(30)

        mock_client.messages.create.assert_called_once_with(
            body='Async foo',
            to='+15555555555',
            from_='+19999999999')

    def test_look_up_number(self):
        # Arrange
        mock_client = MagicMock()
        mock_client.phone_numbers.get.return_value = 'lookup info'

        # Act
        with patch('app.utils.TwilioLookupsClient', return_value=mock_client):
            result = look_up_number('+15555555555')

        # Assert
        self.assertEqual(result, 'lookup info')
        mock_client.phone_numbers.get.assert_called_once_with('+15555555555', include_carrier_info=True)

    def test_look_up_number_error(self):
        # Arrange
        mock_client = MagicMock()
        mock_client.phone_numbers.get.side_effect = TwilioRestException('foo', 'bar')

        # Act
        with patch('app.utils.TwilioLookupsClient', return_value=mock_client):
            result = look_up_number('+15555555555')

        # Assert
        self.assertIsNone(result)
        mock_client.phone_numbers.get.assert_called_once_with('+15555555555', include_carrier_info=True)


    def test_set_twilio_urls_all(self):
        # Arrange
        mock_number = MagicMock()
        mock_number.voice_url = None
        mock_number.sms_url = None
        mock_number.voice_fallback_url = None
        mock_number.sms_fallback_url = None

        mock_client = MagicMock()
        mock_client.phone_numbers.list.return_value = [mock_number]

        # Act
        with patch('app.utils.TwilioRestClient', return_value=mock_client):
            set_twilio_number_urls()

        # Assert
        mock_number.update.assert_called_once_with(
            voice_url='http://localhost/call',
            voice_method='POST',
            sms_url='http://localhost/sms',
            sms_method='POST',
            voice_fallback_url=self.app.config['VOICE_FALLBACK_URL'],
            voice_fallback_method='GET',
            sms_fallback_url=self.app.config['SMS_FALLBACK_URL'],
            sms_fallback_method='GET')

    def test_set_twilio_urls_none(self):
        # Arrange
        mock_number = MagicMock()
        mock_number.voice_url = 'http://example.com/call'
        mock_number.sms_url = 'http://example.com/sms'
        mock_number.voice_fallback_url = 'http://example.com/voice-error'
        mock_number.sms_fallback_url = 'http://example.com/sms-error'

        mock_client = MagicMock()
        mock_client.phone_numbers.list.return_value = [mock_number]

        # Act
        with patch('app.utils.TwilioRestClient', return_value=mock_client):
            set_twilio_number_urls()

        # Assert
        self.assertFalse(mock_number.update.called)
