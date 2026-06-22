from cryptography.fernet import Fernet
from src.domain.ports.data_encryptor import DataEncryptor

class FernetEncryptor(DataEncryptor):
    def __init__(self, encryption_key: str):
        key = encryption_key
        self._fernet = Fernet(key.encode())

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return plain_text
        return self._fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        if not cipher_text:
            return cipher_text
        return self._fernet.decrypt(cipher_text.encode()).decode()