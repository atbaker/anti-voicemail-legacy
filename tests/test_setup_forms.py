import unittest
from unittest.mock import MagicMock
from wtforms.validators import ValidationError

from app.setup.forms import validate_phone_number


class FormsTestCase(unittest.TestCase):

    def test_validate_number(self):
        # Arrange
        mock_field = MagicMock(data='415 555 5555')
        mock_form = MagicMock()
        mock_form.default_region_code.data = 'US'

        # Act
        validate_phone_number(mock_form, mock_field)

        # Assert
        self.assertEqual(mock_field.data, '+14155555555')

    def test_validate_bad_number(self):
        # Arrange
        mock_field = MagicMock(data='555 555')
        mock_form = MagicMock()
        mock_form.default_region_code.data = 'US'

        # Act
        with self.assertRaises(ValidationError):
            validate_phone_number(mock_form, mock_field)

    def test_validate_really_bad_number(self):
        # Arrange
        mock_field = MagicMock(data='abc')
        mock_form = MagicMock()
        mock_form.default_region_code.data = 'US'

        # Act
        with self.assertRaises(ValidationError):
            validate_phone_number(mock_form, mock_field)
