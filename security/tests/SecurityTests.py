import unittest
import requests
import jwt
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os

# Constants for encryption
ENCRYPTION_KEY = os.urandom(32)
IV = os.urandom(16)

# Security endpoints to be tested
BASE_URL = 'https://website.com/api'
AUTH_ENDPOINT = f'{BASE_URL}/auth'
ENCRYPTION_ENDPOINT = f'{BASE_URL}/encrypt'
FIREWALL_TEST_URL = f'{BASE_URL}/firewall/test'

# JWT Token for testing authentication
JWT_SECRET = "secret"
JWT_ALGORITHM = "HS256"

# Penetration test payloads
SQL_INJECTION_PAYLOAD = "' OR '1'='1'; --"
XSS_PAYLOAD = "<script>alert('XSS')</script>"

class SecurityTests(unittest.TestCase):

    def setUp(self):
        # Setup tasks before each test
        self.headers = {'Content-Type': 'application/json'}

    def test_authentication(self):
        """Test authentication using JWT tokens."""
        payload = {"user": "admin", "password": "password123"}
        response = requests.post(AUTH_ENDPOINT, json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        token = response.json().get('token')
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        self.assertEqual(decoded['user'], 'admin')

    def test_invalid_authentication(self):
        """Test authentication with invalid credentials."""
        payload = {"user": "hacker", "password": "wrongpass"}
        response = requests.post(AUTH_ENDPOINT, json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 401)

    def test_rbac(self):
        """Test role-based access control for restricted endpoint."""
        restricted_endpoint = f'{BASE_URL}/admin'
        admin_token = jwt.encode({"role": "admin"}, JWT_SECRET, algorithm=JWT_ALGORITHM)
        user_token = jwt.encode({"role": "user"}, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Admin access
        headers = {'Authorization': f'Bearer {admin_token}'}
        response = requests.get(restricted_endpoint, headers=headers)
        self.assertEqual(response.status_code, 200)

        # User access should be forbidden
        headers = {'Authorization': f'Bearer {user_token}'}
        response = requests.get(restricted_endpoint, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_data_encryption(self):
        """Test data encryption and decryption."""
        data = b'Sensitive information'
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(IV), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Decrypt data
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

        self.assertEqual(data, unpadded_data)

    def test_firewall_rules(self):
        """Test firewall rules by attempting requests blocked by firewall."""
        response = requests.get(FIREWALL_TEST_URL)
        self.assertEqual(response.status_code, 403)

    def test_sql_injection(self):
        """Test for SQL Injection vulnerability."""
        payload = {"username": SQL_INJECTION_PAYLOAD, "password": "irrelevant"}
        response = requests.post(AUTH_ENDPOINT, json=payload, headers=self.headers)
        self.assertNotEqual(response.status_code, 200, "SQL Injection succeeded!")

    def test_xss_vulnerability(self):
        """Test for Cross-site Scripting (XSS) vulnerability."""
        xss_endpoint = f'{BASE_URL}/comments'
        payload = {"comment": XSS_PAYLOAD}
        response = requests.post(xss_endpoint, json=payload, headers=self.headers)
        self.assertNotIn(XSS_PAYLOAD, response.text, "XSS vulnerability found!")

    def test_brute_force_protection(self):
        """Test brute-force attack prevention."""
        for _ in range(10):  # Simulating multiple login attempts
            payload = {"user": "admin", "password": "wrongpassword"}
            response = requests.post(AUTH_ENDPOINT, json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 429, "Brute-force protection not working!")

    def test_token_expiry(self):
        """Test token expiration handling."""
        expired_token = jwt.encode({"exp": 0}, JWT_SECRET, algorithm=JWT_ALGORITHM)
        headers = {'Authorization': f'Bearer {expired_token}'}
        response = requests.get(f'{BASE_URL}/protected', headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_ssl_enforcement(self):
        """Test that all endpoints enforce SSL."""
        insecure_url = 'http://website.com/api/protected'
        response = requests.get(insecure_url)
        self.assertEqual(response.status_code, 403, "Insecure connection allowed!")

    def test_hash_integrity(self):
        """Test data integrity using hashing."""
        data = b"Important data"
        data_hash = hashlib.sha256(data).hexdigest()
        
        # Simulate sending and receiving data
        received_data = data 
        received_hash = hashlib.sha256(received_data).hexdigest()
        
        self.assertEqual(data_hash, received_hash, "Data integrity compromised!")

    def test_token_signature_validation(self):
        """Test for token signature validation."""
        malicious_token = jwt.encode({"user": "admin"}, "wrong_secret", algorithm=JWT_ALGORITHM)
        headers = {'Authorization': f'Bearer {malicious_token}'}
        response = requests.get(f'{BASE_URL}/protected', headers=headers)
        self.assertEqual(response.status_code, 401, "Invalid token accepted!")

if __name__ == '__main__':
    unittest.main()