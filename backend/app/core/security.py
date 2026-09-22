import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import JWTError, jwt
from app.core.config import settings


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(mobile: str, otp: str) -> str:
    """Hash OTP combined with mobile number and server secret key using HMAC-SHA256."""
    key = settings.SECRET_KEY.encode("utf-8")
    message = f"{mobile}:{otp}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_otp_hash(mobile: str, otp: str, expected_hash: str) -> bool:
    """Securely compare hashed OTP in constant time."""
    computed_hash = hash_otp(mobile, otp)
    return hmac.compare_digest(computed_hash, expected_hash)


def generate_whatsapp_login_token() -> str:
    """Generate a cryptographically secure random token with at least 256 bits of entropy."""
    return secrets.token_urlsafe(32)


def hash_whatsapp_token(token: str) -> str:
    """Hash WhatsApp login token with server secret key using HMAC-SHA256."""
    key = settings.SECRET_KEY.encode("utf-8")
    message = token.strip().encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_whatsapp_token_hash(token: str, expected_hash: str) -> bool:
    """Securely compare WhatsApp login token hash in constant time."""
    computed_hash = hash_whatsapp_token(token)
    return hmac.compare_digest(computed_hash, expected_hash)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "token_type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a long-lived JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "token_type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_verification_token(
    mobile: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed verification token proving OTP was verified for this mobile."""
    to_encode = {
        "sub": mobile,
        "purpose": "otp_verified",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid or expired token: {str(e)}")
