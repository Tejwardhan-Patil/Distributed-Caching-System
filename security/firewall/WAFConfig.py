import re
import json
import logging
import hashlib
import time
import jwt
from flask import Flask, request, abort
from RBAC import RBAC
from tlsconfig import setup_tls

# Set up logging
logging.basicConfig(filename="waf.log", level=logging.INFO, format="%(asctime)s %(message)s")

app = Flask(__name__)
rbac = RBAC()

# Allowed HTTP methods
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

# Define common attack patterns for SQL Injection, XSS, and others
SQLI_PATTERNS = [r"(\%27)|(\')|(\-\-)|(\%23)|(#)", r"((\%3D)|(=))[^\n]*(\%27|\'|\-\-|\%3B|;)", r"w*(\%27|')\s*or\s*.+\s*=\s*(\%27|')"]
XSS_PATTERNS = [r"(<|%3C)[^\n]+(>|%3E)", r"(javascript:|vbscript:|data:)", r"(<script>.+?</script>)"]

# JWT Secret Key (should be stored securely)
JWT_SECRET = "mysecretkey"

# API Rate Limit configuration
RATE_LIMIT = 100  # Max requests per minute
rate_limit_cache = {}

# Load encryption settings for WAF
setup_tls(app)

# Rate limiting
def check_rate_limit(client_ip):
    if client_ip not in rate_limit_cache:
        rate_limit_cache[client_ip] = {"count": 1, "timestamp": time.time()}
    else:
        time_diff = time.time() - rate_limit_cache[client_ip]["timestamp"]
        if time_diff < 60:
            rate_limit_cache[client_ip]["count"] += 1
        else:
            rate_limit_cache[client_ip]["count"] = 1
            rate_limit_cache[client_ip]["timestamp"] = time.time()

    if rate_limit_cache[client_ip]["count"] > RATE_LIMIT:
        logging.warning(f"Rate limit exceeded for IP: {client_ip}")
        abort(429, "Rate limit exceeded")

# Security: Check for common web attack patterns
def detect_attacks(data):
    for pattern in SQLI_PATTERNS + XSS_PATTERNS:
        if re.search(pattern, data, re.IGNORECASE):
            logging.warning(f"Potential attack detected: {data}")
            abort(403, "Forbidden: Possible attack detected")

# Verify JWT for API authentication
def verify_jwt(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        logging.error("JWT has expired")
        abort(401, "Token has expired")
    except jwt.InvalidTokenError:
        logging.error("Invalid JWT")
        abort(401, "Invalid token")

# Function to generate JWT (For testing purposes)
def generate_jwt(username):
    payload = {"user": username, "exp": time.time() + 3600}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# Input validation for incoming requests
def validate_request(data):
    if not isinstance(data, dict):
        logging.error("Invalid request format")
        abort(400, "Invalid request format")
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, float)):
            logging.error("Invalid data types in request")
            abort(400, "Invalid data format")

# Input sanitization
def sanitize_input(input_data):
    sanitized = re.sub(r'[<>]', '', input_data)  # Sanitization removing HTML tags
    logging.info(f"Sanitized input: {sanitized}")
    return sanitized

# Main WAF route
@app.route("/protected_api", methods=ALLOWED_METHODS)
def protected_api():
    client_ip = request.remote_addr
    check_rate_limit(client_ip)

    # Check for JWT token in the Authorization header
    token = request.headers.get("Authorization")
    if not token:
        abort(401, "Authorization token required")
    verify_jwt(token)

    # Validate and sanitize request data
    if request.method == "POST":
        data = request.get_json()
        validate_request(data)
        sanitized_data = {key: sanitize_input(value) for key, value in data.items()}
        detect_attacks(json.dumps(sanitized_data))

    logging.info(f"Request from {client_ip} allowed")
    return "Request successfully processed", 200

# IP blacklisting mechanism
BLACKLIST = {"192.168.1.10", "10.0.0.5"} 

@app.before_request
def block_blacklisted_ips():
    client_ip = request.remote_addr
    if client_ip in BLACKLIST:
        logging.warning(f"Blocked request from blacklisted IP: {client_ip}")
        abort(403, "Forbidden: Blacklisted IP")

# Content Security Policy (CSP) Headers for XSS Mitigation
@app.after_request
def set_csp_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Role-based Access Control
@app.route("/admin", methods=["GET"])
def admin_route():
    token = request.headers.get("Authorization")
    if not token:
        abort(401, "Authorization token required")
    user = verify_jwt(token)

    # Check user's role using RBAC
    if not rbac.has_permission(user["user"], "admin"):
        logging.warning(f"User {user['user']} attempted unauthorized access")
        abort(403, "Forbidden: You don't have the required permissions")
    return "Welcome Admin", 200

# Logging request information for auditing
@app.after_request
def log_request(response):
    client_ip = request.remote_addr
    logging.info(f"Request from {client_ip} with status {response.status}")
    return response

# Load firewall rules from file
def load_firewall_rules():
    try:
        with open("firewall_rules.json", "r") as rules_file:
            rules = json.load(rules_file)
            logging.info("Firewall rules loaded successfully")
            return rules
    except FileNotFoundError:
        logging.error("Firewall rules file not found")
        return {}

# Check if request complies with firewall rules
def enforce_firewall_rules():
    firewall_rules = load_firewall_rules()
    client_ip = request.remote_addr
    request_path = request.path

    # Enforce rules
    if client_ip in firewall_rules.get("blocked_ips", []):
        logging.warning(f"IP {client_ip} is blocked")
        abort(403, "Forbidden: Your IP is blocked")
    if request_path in firewall_rules.get("blocked_paths", []):
        logging.warning(f"Path {request_path} is blocked")
        abort(403, "Forbidden: Access to this path is blocked")

# Run the WAF
if __name__ == "__main__":
    app.run(ssl_context=("cert.pem", "key.pem"), host="0.0.0.0", port=443)