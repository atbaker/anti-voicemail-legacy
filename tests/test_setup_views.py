import unittest
from flask import current_app
from unittest.mock import MagicMock, patch

from app import create_app, db
from app.models import Mailbox, Voicemail


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

    def test_sms_no_mailbox(self):
        # Arrange
        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Foo Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/sms', data={'From': '+15555555555'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mailbox = Mailbox.query.one()
        self.assertEqual(mailbox.phone_number, '+15555555555')

        content = str(response.data)
        self.assertIn("Hi there!", content)

    def test_sms_no_second_mailbox(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        response = self.test_client.post('/sms', data={'From': '+16666666666'})

        # Assert
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Mailbox.query.count(), 1)

    def test_sms_config_image(self):
        # Act
        with patch('app.setup.views._import_config', return_value='Image processed!') as mock:
            response = self.test_client.post('/sms', data={
            'MediaUrl0': 'http://i.imgur.com/VMSuO1N.gif'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with()

        content = str(response.data)
        self.assertIn('Image processed!', content)

    def test_sms_disable_command(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Verizon Wireless')
        db.session.add(mailbox)

        # Act
        response = self.test_client.post('/sms', data={
            'From': '+15555555555',
            'Body': 'disable'})

        # Assert
        self.assertEqual(response.status_code, 200)

        content = str(response.data)
        self.assertIn('*73', content)

    def test_sms_reset_command(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Arrange
        mock_lookup_result = MagicMock()
        mock_lookup_result.carrier = {'name': 'Bar Wireless'}

        # Act
        with patch('app.models.look_up_number', return_value=mock_lookup_result):
            response = self.test_client.post('/sms', data={
                'From': '+15555555555',
                'Body': 'reset'})

        # Assert
        self.assertEqual(response.status_code, 200)

        content = str(response.data)
        self.assertIn('Bzzzzt!', content)

        mailboxes = Mailbox.query.all()
        self.assertEqual(len(mailboxes), 1)
        self.assertEqual(mailboxes[0].carrier, 'Bar Wireless')

    def test_sms_process_answer(self):
        # Arrange
        mailbox = Mailbox(phone_number='+15555555555', carrier='Foo Wireless')
        db.session.add(mailbox)

        # Act
        with patch('app.setup.views._process_answer', return_value='Answer processed!') as mock:
            response = self.test_client.post('/sms', data={
                'From': '+15555555555',
                'Body': 'Jane Foo'})

        # Assert
        self.assertEqual(response.status_code, 200)
        mock.assert_called_once_with('Jane Foo', mailbox)

        content = str(response.data)
        self.assertIn('Answer processed!', content)
