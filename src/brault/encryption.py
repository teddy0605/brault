import logging
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken

class EncryptionManager:
    def __init__(self, encryption_key):
            logging.debug("ENTERING ENCRYPTION MANAGER")
            key_hash = hashlib.sha256(encryption_key.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key_hash)
            self.fernet = Fernet(fernet_key)

    def encrypt_data(self, data):
        try:
            return self.fernet.encrypt(data.encode('utf-8'))
        except InvalidToken as e:
            logging.error("Encryption failed: %s", e)
            raise

    def decrypt_data(self, data):
        try:
            return self.fernet.decrypt(data).decode('utf-8')
        except InvalidToken:
            logging.error("Decryption failed. The encryption key is incorrect or the data is corrupted.")
            raise