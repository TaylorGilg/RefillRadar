import os
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet
from typing import Optional

class OfflineAuthenticator:
    def __init__(self, app_secret_key: Optional[str] = None):
        """
        Initialize secure offline authentication
        
        Args:
            app_secret_key (str, optional): Custom secret key for enhanced security
        """
        # Use provided key or generate a secure one
        self.app_secret_key = app_secret_key or secrets.token_hex(32)
        
        # Create encryption key from secret
        self.encryption_key = self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _generate_encryption_key(self) -> bytes:
        """
        Generate a secure encryption key from the app secret
        
        Returns:
            bytes: Base64 encoded encryption key
        """
        # Use SHA-256 to derive a consistent key
        key_bytes = hashlib.sha256(self.app_secret_key.encode()).digest()
        return base64.urlsafe_b64encode(key_bytes)
    
    def hash_password(self, password: str) -> str:
        """
        Create a secure password hash
        
        Args:
            password (str): User's password
        
        Returns:
            str: Securely hashed password
        """
        # Use key stretching and salt
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode(), 
            salt.encode(), 
            100000
        )
        return f"{salt}${key.hex()}"
    
    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """
        Verify a password against its stored hash
        
        Args:
            stored_password (str): Stored password hash
            provided_password (str): Password to verify
        
        Returns:
            bool: Whether password is correct
        """
        try:
            salt, stored_key = stored_password.split('$')
            verified_key = hashlib.pbkdf2_hmac(
                'sha256', 
                provided_password.encode(), 
                salt.encode(), 
                100000
            )
            return secrets.compare_digest(verified_key.hex(), stored_key)
        except:
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive user data
        
        Args:
            data (str): Data to encrypt
        
        Returns:
            str: Encrypted data
        """
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive user data
        
        Args:
            encrypted_data (str): Encrypted data to decrypt
        
        Returns:
            str: Decrypted data
        """
        return self.cipher.decrypt(encrypted_data.encode()).decode()
