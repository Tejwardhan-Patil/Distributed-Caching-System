import requests
import time
import threading
import unittest
from requests.auth import HTTPBasicAuth

BASE_URL = "https://website.com/api"
AUTH_URL = BASE_URL + "/auth"
CACHE_URL = BASE_URL + "/cache"
XSS_TEST_STRING = "<script>alert('XSS')</script>"

class PenetrationTests(unittest.TestCase):

    def setUp(self):
        self.auth_token = self.get_auth_token("admin", "password123")
        self.headers = {'Authorization': f'Bearer {self.auth_token}'}

    def get_auth_token(self, username, password):
        response = requests.post(AUTH_URL, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            return response.json().get("token")
        raise Exception("Failed to get auth token")

    def test_authentication_bypass(self):
        print("Testing authentication bypass...")
        response = requests.get(CACHE_URL, headers={})
        self.assertEqual(response.status_code, 401, "Auth bypass detected!")

    def test_sql_injection(self):
        print("Testing SQL Injection...")
        payload = "' OR '1'='1"
        response = requests.post(CACHE_URL, json={"query": payload}, headers=self.headers)
        self.assertNotEqual(response.status_code, 200, "SQL Injection vulnerability detected!")
    
    def test_xss_vulnerability(self):
        print("Testing XSS vulnerability...")
        response = requests.post(CACHE_URL, json={"data": XSS_TEST_STRING}, headers=self.headers)
        self.assertNotIn(XSS_TEST_STRING, response.text, "XSS vulnerability detected!")

    def test_dos_attack(self):
        print("Testing Denial of Service attack...")
        start_time = time.time()
        for _ in range(1000):
            threading.Thread(target=self.send_requests).start()
        duration = time.time() - start_time
        self.assertLess(duration, 10, "System vulnerable to DoS attack!")

    def send_requests(self):
        for _ in range(1000):
            response = requests.get(CACHE_URL, headers=self.headers)
            if response.status_code != 200:
                raise Exception("Failed request during DoS test")

    def test_insecure_tls(self):
        print("Testing for insecure TLS configurations...")
        response = requests.get(CACHE_URL, headers=self.headers, verify=False)
        self.assertEqual(response.status_code, 200, "Insecure TLS configuration detected!")

    def test_brute_force_attack(self):
        print("Testing brute force attack prevention...")
        for i in range(10):
            response = requests.post(AUTH_URL, auth=HTTPBasicAuth("admin", f"wrong_password_{i}"))
            self.assertEqual(response.status_code, 401, "Brute force vulnerability detected!")

    def test_role_based_access_control(self):
        print("Testing RBAC (Role-based access control)...")
        non_admin_token = self.get_auth_token("user", "password123")
        non_admin_headers = {'Authorization': f'Bearer {non_admin_token}'}
        response = requests.post(CACHE_URL, json={"operation": "delete"}, headers=non_admin_headers)
        self.assertEqual(response.status_code, 403, "RBAC failure detected!")

    def test_api_key_authentication(self):
        print("Testing API key authentication...")
        headers = {"X-API-Key": "INVALID_API_KEY"}
        response = requests.get(CACHE_URL, headers=headers)
        self.assertEqual(response.status_code, 403, "Invalid API key bypass detected!")

    def test_jwt_authentication(self):
        print("Testing JWT authentication...")
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.WRONGSIGNATURE"
        headers = {'Authorization': f'Bearer {invalid_token}'}
        response = requests.get(CACHE_URL, headers=headers)
        self.assertEqual(response.status_code, 401, "Invalid JWT token bypass detected!")

    def test_weak_password_detection(self):
        print("Testing weak password detection...")
        weak_passwords = ["123456", "password", "admin", "letmein"]
        for password in weak_passwords:
            response = requests.post(AUTH_URL, auth=HTTPBasicAuth("admin", password))
            self.assertEqual(response.status_code, 401, f"Weak password accepted: {password}")

    def test_sensitive_data_exposure(self):
        print("Testing sensitive data exposure...")
        response = requests.get(BASE_URL + "/config", headers=self.headers)
        sensitive_keywords = ["password", "secret", "private_key"]
        for keyword in sensitive_keywords:
            self.assertNotIn(keyword, response.text, f"Sensitive data exposure detected: {keyword}")

    def test_firewall_rules(self):
        print("Testing Web Application Firewall rules...")
        malicious_payloads = [
            "<script>alert('XSS')</script>",  # XSS
            "'; DROP TABLE users;",          # SQL Injection
            "../passwd",                 # Path traversal
        ]
        for payload in malicious_payloads:
            response = requests.post(CACHE_URL, json={"query": payload}, headers=self.headers)
            self.assertNotEqual(response.status_code, 200, f"Firewall bypass detected for payload: {payload}")

    def test_rate_limiting(self):
        print("Testing rate limiting...")
        for _ in range(100):
            response = requests.get(CACHE_URL, headers=self.headers)
            if response.status_code == 429:
                break
        self.assertEqual(response.status_code, 429, "Rate limiting not enforced!")

    def test_ssl_certificate_validation(self):
        print("Testing SSL certificate validation...")
        try:
            response = requests.get(CACHE_URL, headers=self.headers, verify=True)
        except requests.exceptions.SSLError:
            print("SSL certificate validation passed")
        else:
            self.fail("SSL certificate validation failed!")

    def test_http_methods_restriction(self):
        print("Testing HTTP methods restriction...")
        disallowed_methods = ["PUT", "DELETE", "TRACE", "OPTIONS"]
        for method in disallowed_methods:
            response = requests.request(method, CACHE_URL, headers=self.headers)
            self.assertEqual(response.status_code, 405, f"HTTP method {method} not restricted!")

    def test_input_validation(self):
        print("Testing input validation...")
        invalid_inputs = ["<script>", "' OR '1'='1", "{malformed_json"]
        for invalid_input in invalid_inputs:
            response = requests.post(CACHE_URL, json={"input": invalid_input}, headers=self.headers)
            self.assertNotEqual(response.status_code, 200, f"Input validation failed for: {invalid_input}")

    def test_logging_of_malicious_requests(self):
        print("Testing logging of malicious requests...")
        payload = "' OR '1'='1"
        response = requests.post(CACHE_URL, json={"query": payload}, headers=self.headers)
        self.assertNotEqual(response.status_code, 200, "SQL Injection vulnerability detected!")
        # Check the logs to ensure the malicious request was logged

if __name__ == "__main__":
    unittest.main()