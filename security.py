from argon2 import PasswordHasher
from cryptography.fernet import Fernet

_ph = PasswordHasher()


def hash_password(p: str) -> str:
    return _ph.hash(p)


def verify_password(h: str, p: str) -> bool:
    try:
        return _ph.verify(h, p)
    except Exception:
        return False


def encrypt_secret(key: str, plaintext: str) -> str:
    return Fernet(key.encode()).encrypt(plaintext.encode()).decode()


def decrypt_secret(key: str, ciphertext: str) -> str:
    return Fernet(key.encode()).decrypt(ciphertext.encode()).decode()
