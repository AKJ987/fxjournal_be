import re
import os
import base64
import secrets
from django.utils import timezone
from Crypto.Cipher import AES

def is_password_valid(password):
    password_regex = (
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)"
        r"(?=.*[@$!%*?&^#()_+\-=])[A-Za-z\d@$!%*?&^#()_+\-=]{8,}$"
    )
    if not re.match(password_regex, password):
        return False

    return True

def get_secret_key():
    BLOCK_SIZE = 32
    secret = os.urandom(BLOCK_SIZE)
    return secret

def encrypt_data(string, key):   
    BLOCK_SIZE = 32
    PADDING = '{'.encode()
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    cipher = AES.new(key,AES.MODE_ECB)
    encoded = EncodeAES(cipher, string)
    return encoded

def decrypt_data(encoded, key):
    decoded = ''
    try:
        PADDING = '{'.encode()
        DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
        cipher = AES.new(key, AES.MODE_ECB)
        decoded = DecodeAES(cipher, encoded)
    except:
        pass
    return decoded

def generate_otp(user):
    otp = str(secrets.randbelow(900000) + 100000)
    key = get_secret_key()
    user.otp = encrypt_data(otp.encode('utf-8'), key).decode()
    user.otp_created_time = timezone.now()
    user.secret_key = base64.b64encode(key).decode()
    user.save(update_fields=["otp", "otp_created_time", "secret_key"])
    return otp
