"""
Credential Manager - Handle encryption and decryption of sensitive credentials
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import yaml
import logging

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manage encryption and decryption of platform credentials"""
    
    def __init__(self, config_path="config/platform_credentials.yaml"):
        """
        Initialize credential manager
        
        Args:
            config_path: Path to credentials configuration file
        """
        self.config_path = config_path
        self.credentials = self._load_credentials()
        self.fernet = self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption using environment key or generate new key"""
        encryption_config = self.credentials.get('encryption', {})
        use_env_key = encryption_config.get('use_env_key', True)
        env_key_name = encryption_config.get('env_key_name', 'ENCRYPTION_KEY')
        key_file = encryption_config.get('key_file', 'cache/.encryption_key')
        
        # Try to get key from environment
        if use_env_key and os.getenv(env_key_name):
            key = os.getenv(env_key_name).encode()
            # Ensure key is properly formatted
            if len(key) != 44:  # Fernet key should be 44 bytes when base64 encoded
                # Derive key from password
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'red-clipping-salt',  # In production, use random salt
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(key))
        else:
            # Try to load from file
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                # Ensure directory exists
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                # Save key
                with open(key_file, 'wb') as f:
                    f.write(key)
                logger.info(f"Generated new encryption key at {key_file}")
        
        return Fernet(key)
    
    def _load_credentials(self):
        """Load credentials from YAML file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_credentials(self):
        """Save credentials to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.credentials, f, default_flow_style=False)
    
    def encrypt_credential(self, platform, field, value):
        """
        Encrypt and store a credential
        
        Args:
            platform: Platform name (instagram, youtube, tiktok, github_api)
            field: Field name (username, password, token, etc.)
            value: Value to encrypt
        """
        if not value:
            return
        
        encrypted_value = self.fernet.encrypt(value.encode()).decode()
        
        if platform not in self.credentials:
            self.credentials[platform] = {}
        
        self.credentials[platform][field] = encrypted_value
        self.credentials[platform]['encrypted'] = True
        
        self._save_credentials()
        logger.info(f"Encrypted {field} for {platform}")
    
    def decrypt_credential(self, platform, field):
        """
        Decrypt and retrieve a credential
        
        Args:
            platform: Platform name
            field: Field name
            
        Returns:
            Decrypted credential value or None
        """
        if platform not in self.credentials:
            return None
        
        encrypted_value = self.credentials[platform].get(field)
        if not encrypted_value:
            return None
        
        is_encrypted = self.credentials[platform].get('encrypted', False)
        
        if is_encrypted:
            try:
                return self.fernet.decrypt(encrypted_value.encode()).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt {field} for {platform}: {e}")
                return None
        else:
            # Return as-is if not encrypted
            return encrypted_value
    
    def get_credentials(self, platform):
        """
        Get all credentials for a platform
        
        Args:
            platform: Platform name
            
        Returns:
            Dictionary of decrypted credentials
        """
        if platform not in self.credentials:
            return {}
        
        platform_creds = self.credentials[platform].copy()
        is_encrypted = platform_creds.get('encrypted', False)
        
        # Remove metadata fields
        platform_creds.pop('encrypted', None)
        
        if is_encrypted:
            # Decrypt all fields
            decrypted = {}
            for key, value in platform_creds.items():
                if value:
                    try:
                        decrypted[key] = self.fernet.decrypt(value.encode()).decode()
                    except Exception as e:
                        logger.error(f"Failed to decrypt {key}: {e}")
                        decrypted[key] = None
                else:
                    decrypted[key] = value
            return decrypted
        
        return platform_creds
    
    def set_credential_from_env(self, platform, field, env_var_name):
        """
        Set credential from environment variable
        
        Args:
            platform: Platform name
            field: Field name
            env_var_name: Environment variable name
        """
        value = os.getenv(env_var_name)
        if value:
            self.encrypt_credential(platform, field, value)
            logger.info(f"Set {field} for {platform} from environment variable {env_var_name}")
        else:
            logger.warning(f"Environment variable {env_var_name} not found")
