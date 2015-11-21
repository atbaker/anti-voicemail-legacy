import unittest
from flask import current_app
from twilio.rest.exceptions import TwilioRestException
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.decorators import validate_twilio_request
from app.utils import look_up_number, convert_to_national_format, send_async_message, set_twilio_number_urls


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

    def test_national_format_error(self):
        # Act
        result = convert_to_national_format('8656696')

        # Assert
        self.assertEqual(result, '8656696')

    def test_set_twilio_urls_all(self):
        # Arrange
        mock_number = MagicMock(
            voice_url=None, sms_url=None, voice_fallback_url=None,
            sms_fallback_url=None)

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
        mock_number = MagicMock(
            voice_url='http://example.com/call',
            sms_url='http://example.com/sms',
            voice_fallback_url='http://example.com/voice-error',
            sms_fallback_url='http://example.com/sms-error')

        mock_client = MagicMock()
        mock_client.phone_numbers.list.return_value = [mock_number]

        # Act
        with patch('app.utils.TwilioRestClient', return_value=mock_client):
            set_twilio_number_urls()

        # Assert
        self.assertFalse(mock_number.update.called)

    def test_set_twilio_urls_https(self):
        # Arrange
        mock_number = MagicMock(voice_url=None, sms_url=None)

        mock_client = MagicMock()
        mock_client.phone_numbers.list.return_value = [mock_number]

        # Act
        with patch('app.utils.TwilioRestClient', return_value=mock_client):
            with patch('app.utils.request') as mock_request:
                mock_request.scheme = 'https'
                set_twilio_number_urls()

        # Assert
        mock_number.update.assert_called_once_with(
            voice_url='https://localhost/call',
            voice_method='POST',
            sms_url='https://localhost/sms',
            sms_method='POST')


class DecoratorsTestCase(unittest.TestCase):
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

    def test_valid_request(self):
        # Act
        response = self.test_client.post('/call', data={
            'ForwardedFrom': '+15555555555',
            'From': '+17777777777'
            })

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_invalid_request(self):
        # Act
        response = self.test_client.post('/call', data={
            'ForwardedFrom': '+15555555555',
            'From': '+17777777777'
            }, headers={'FORCE_VALIDATION': True})

        # Assert
        self.assertEqual(response.status_code, 403)

    def test_x_forwarded_proto_request(self):
        # Arrange
        mock_validator = MagicMock()

        # Act
        with patch('app.decorators.RequestValidator', return_value=mock_validator):
            response = self.test_client.post('/call', data={
                'ForwardedFrom': '+15555555555',
                'From': '+17777777777'
                }, headers={'X-Forwarded-Proto': 'https'})

        # Assert
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            mock_validator.validate.call_args[0][0], 'https://localhost/call')
