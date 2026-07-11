from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib
from app.config import settings

# Configure passlib for bcrypt password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash from a plain text password."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# --- API Key encryption at rest ---
def _get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance derived from the configured encryption key, or None if not set."""
    key = settings.API_KEY_ENCRYPTION_KEY
    if not key:
        return None
    # Derive a 32-byte key from the configured secret via SHA256 + base64
    digest = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def encrypt_api_key(plain_key: Optional[str]) -> Optional[str]:
    """Encrypt an API key before storing. Returns None if key is empty or encryption unavailable."""
    if not plain_key:
        return None
    f = _get_fernet()
    if not f:
        return plain_key  # no encryption configured; store as-is
    return f.encrypt(plain_key.encode()).decode()


def decrypt_api_key(encrypted_key: Optional[str]) -> Optional[str]:
    """Decrypt an API key for use. Returns None if key is empty or decryption unavailable."""
    if not encrypted_key:
        return None
    f = _get_fernet()
    if not f:
        # If the value looks like a Fernet token (starts with 'gAAAAA') but we have no key, it's encrypted and we can't read it
        if encrypted_key.startswith("gAAAAA"):
            return None
        return encrypted_key  # stored as plaintext (legacy or no encryption configured)
    try:
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        # Decryption failed — possibly plaintext from before encryption was enabled
        return encrypted_key

