"""
GETOLS Security Module
Handles password hashing, credential encryption (AES-256-GCM), and validation.
"""

import os
import re
import base64
import secrets
from typing import Tuple, Optional
from datetime import datetime, timedelta

import bcrypt
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core import settings


# ============================================
# PASSWORD HASHING (using bcrypt directly)
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


# ============================================
# PASSWORD POLICY VALIDATION
# ============================================

def validate_password_policy(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password against policy:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    return True, None


# ============================================
# AES-256-GCM ENCRYPTION
# ============================================

def get_encryption_key() -> bytes:
    """Get the encryption key from settings (32 bytes for AES-256)."""
    key = settings.encryption_key
    # Ensure key is 32 bytes
    if len(key) < 32:
        key = key.ljust(32, '0')
    elif len(key) > 32:
        key = key[:32]
    return key.encode('utf-8')


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a credential using AES-256-GCM.
    
    Returns:
        Base64-encoded string containing nonce + tag + ciphertext
    """
    if not plaintext:
        return ""
    
    key = get_encryption_key()
    nonce = get_random_bytes(12)  # GCM standard nonce size
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    
    # Combine nonce + tag + ciphertext
    encrypted_data = nonce + tag + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_credential(encrypted: str) -> str:
    """
    Decrypt a credential encrypted with AES-256-GCM.
    
    Returns:
        Decrypted plaintext string
    """
    if not encrypted:
        return ""
    
    try:
        key = get_encryption_key()
        encrypted_data = base64.b64decode(encrypted.encode('utf-8'))
        
        # Extract nonce (12 bytes), tag (16 bytes), and ciphertext
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential: {str(e)}")


# ============================================
# SESSION MANAGEMENT
# ============================================

def get_serializer() -> URLSafeTimedSerializer:
    """Get the session serializer."""
    return URLSafeTimedSerializer(settings.secret_key)


def create_session_token(user_id: int, username: str, role: str) -> str:
    """Create a new session token."""
    serializer = get_serializer()
    data = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "created_at": datetime.utcnow().isoformat()
    }
    return serializer.dumps(data)


def verify_session_token(token: str) -> Optional[dict]:
    """
    Verify and decode a session token.
    
    Returns:
        Session data dict or None if invalid/expired
    """
    serializer = get_serializer()
    try:
        # Max age in seconds (convert minutes to seconds)
        max_age = settings.session_lifetime * 60
        data = serializer.loads(token, max_age=max_age)
        return data
    except (BadSignature, SignatureExpired):
        return None


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return secrets.token_urlsafe(32)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def generate_random_password(length: int = 12) -> str:
    """Generate a random password that meets policy requirements."""
    import string
    
    # Ensure at least one of each required type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    
    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits
    password.extend(secrets.choice(all_chars) for _ in range(length - 3))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)
