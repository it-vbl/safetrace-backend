import re
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator


def validate_indonesian_phone_number(value):
    """Validate Indonesian phone number format.
    
    Validates that the phone number follows Indonesian phone number conventions.
    Accepts numbers starting with +62 or 0, followed by 8, and 8-11 additional digits.
    Removes spaces, hyphens, and periods before validation.

    Args:
        value (str): Phone number string to validate

    Raises:
        ValidationError: If the phone number format is invalid
    """
    
    number = re.sub(r'[\s\-.]', '', value)
    pattern = re.compile(r'^(\+62|0)8[1-9][0-9]{6,11}$')

    if not pattern.match(number):
        raise ValidationError("Nomor telepon tidak valid. Harus dimulai dengan +62 atau 0 dan diikuti "
                              "oleh 8 dan 8-11 digit lainnya.", params={'value': value})


class MaxSizeFileValidator(BaseValidator):
    """Validator for maximum file size.

    Args:
        BaseValidator (django.core.validators.BaseValidator): Base class for validators.

    Returns:
        None
    """
    message = "Ukuran file terlalu besar. Maksimal %(limit_value)s MB"
    code = "file_size_exceeded"

    def compare(self, value, limit):
        # Konversi MB ke Byte
        bytes_value = limit * 1024 * 1024
        return value.size > bytes_value
