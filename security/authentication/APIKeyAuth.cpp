#include <iostream>
#include <unordered_map>
#include <string>
#include <vector>
#include <ctime>
#include <openssl/sha.h> 

// Secure API Key Store Class
class SecureAPIKeyStore {
public:
    SecureAPIKeyStore() {
        apiKeyStore["user1"] = hashKey("123456789user1");
        apiKeyStore["user2"] = hashKey("abcdefghiuser2");
    }

    bool validateKey(const std::string& userId, const std::string& apiKey) {
        auto it = apiKeyStore.find(userId);
        if (it != apiKeyStore.end()) {
            std::string hashedInputKey = hashKey(apiKey);
            return (it->second == hashedInputKey);
        }
        return false;
    }

private:
    std::unordered_map<std::string, std::string> apiKeyStore;

    // Function to hash the API key for storage and comparison
    std::string hashKey(const std::string& key) {
        unsigned char hash[SHA256_DIGEST_LENGTH];
        SHA256(reinterpret_cast<const unsigned char*>(key.c_str()), key.length(), hash);
        std::string hashedKey;
        for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
            hashedKey += sprintf("%02x", hash[i]);
        }
        return hashedKey;
    }
};

// Authentication Middleware for API requests
class APIKeyAuthMiddleware {
public:
    APIKeyAuthMiddleware() : keyStore() {}

    // Authenticate the API key for a given user
    bool authenticate(const std::string& userId, const std::string& apiKey) {
        return keyStore.validateKey(userId, apiKey);
    }

private:
    SecureAPIKeyStore keyStore;
};

// Class to represent API requests
class APIRequest {
public:
    APIRequest(const std::string& userId, const std::string& apiKey)
        : userId(userId), apiKey(apiKey) {}

    std::string getUserId() const { return userId; }
    std::string getAPIKey() const { return apiKey; }

private:
    std::string userId;
    std::string apiKey;
};

// API Controller to handle incoming API requests
class APIController {
public:
    APIController() : authMiddleware() {}

    // Process an API request
    void processRequest(const APIRequest& request) {
        if (authMiddleware.authenticate(request.getUserId(), request.getAPIKey())) {
            std::cout << "Request authenticated for user: " << request.getUserId() << std::endl;
            // Proceed with the request processing
        } else {
            std::cerr << "Authentication failed for user: " << request.getUserId() << std::endl;
        }
    }

private:
    APIKeyAuthMiddleware authMiddleware;
};

// Helper function to generate an API key
std::string generateAPIKey(const std::string& userId) {
    std::string base = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    std::string apiKey;
    srand(static_cast<unsigned>(time(0)));
    for (int i = 0; i < 20; ++i) {
        apiKey += base[rand() % base.length()];
    }
    apiKey += userId; // Append userId for association
    return apiKey;
}

// Main function to test the API key authentication system
int main() {
    APIController apiController;

    // Generate some API keys for users
    std::string apiKey1 = generateAPIKey("user1");
    std::string apiKey2 = generateAPIKey("user2");

    std::cout << "Generated API Key for user1: " << apiKey1 << std::endl;
    std::cout << "Generated API Key for user2: " << apiKey2 << std::endl;

    // Creating API requests with valid and invalid keys
    APIRequest validRequest("user1", apiKey1);
    APIRequest invalidRequest("user2", "invalidKey12345");

    // Processing requests
    apiController.processRequest(validRequest);
    apiController.processRequest(invalidRequest);

    return 0;
}