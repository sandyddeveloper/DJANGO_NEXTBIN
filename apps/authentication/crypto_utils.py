import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def get_fernet_key():
    # Derive a 32-byte key from settings.SECRET_KEY
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_value(value):
    if not value:
        return ""
    f = Fernet(get_fernet_key())
    return f.encrypt(value.encode()).decode()


def decrypt_value(token):
    if not token:
        return ""
    f = Fernet(get_fernet_key())
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        return ""


def hash_value(value):
    if not value:
        return ""
    h = hashlib.sha256((value + settings.SECRET_KEY).encode())
    return h.hexdigest()


def mask_email(email):
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    name, domain = parts[0], parts[1]
    if len(name) > 2:
        masked_name = name[:2] + '*' * (len(name) - 2)
    else:
        masked_name = name[0] + '*'
    return f"{masked_name}@{domain}"


def mask_mobile(mobile):
    if not mobile:
        return ""
    if len(mobile) > 4:
        return '*' * (len(mobile) - 4) + mobile[-4:]
    return '*' * len(mobile)


def mask_password(password):
    return '********'


def mask_pin(pin):
    return '******'


class EncryptedTextField(models.TextField):
    """
    A custom Django field that encrypts text values on database write
    and decrypts them transparently on database read.
    """
    def get_prep_value(self, value):
        prep_value = super().get_prep_value(value)
        if prep_value:
            # Avoid double encryption if it's already a Fernet token
            if str(prep_value).startswith('gAAAAA'):
                return prep_value
            return encrypt_value(str(prep_value))
        return prep_value

    def from_db_value(self, value, expression, connection):
        if value:
            # If it starts with Fernet prefix, decrypt it
            if str(value).startswith('gAAAAA'):
                return decrypt_value(value)
            return value
        return value

    def to_python(self, value):
        if isinstance(value, str):
            return value
        return super().to_python(value)
