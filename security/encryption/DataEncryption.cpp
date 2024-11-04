#include <openssl/conf.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/aes.h>
#include <iostream>
#include <cstring>
#include <string>
#include <vector>

class DataEncryption {
private:
    unsigned char key[32]; // 256-bit AES key
    unsigned char iv[16];  // 128-bit IV for AES

    void handleErrors() {
        ERR_print_errors_fp(stderr);
        abort();
    }

public:
    DataEncryption(const std::string& keyStr, const std::string& ivStr) {
        if (keyStr.size() == 32 && ivStr.size() == 16) {
            memcpy(key, keyStr.c_str(), 32);
            memcpy(iv, ivStr.c_str(), 16);
        } else {
            throw std::invalid_argument("Key or IV size is incorrect");
        }
    }

    // Encrypt data
    std::vector<unsigned char> encrypt(const std::string& plaintext) {
        EVP_CIPHER_CTX* ctx;

        int len;
        int ciphertext_len;

        std::vector<unsigned char> ciphertext(plaintext.size() + AES_BLOCK_SIZE);

        if (!(ctx = EVP_CIPHER_CTX_new())) handleErrors();

        if (1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv))
            handleErrors();

        if (1 != EVP_EncryptUpdate(ctx, ciphertext.data(), &len,
                                   reinterpret_cast<const unsigned char*>(plaintext.c_str()), plaintext.size()))
            handleErrors();
        ciphertext_len = len;

        if (1 != EVP_EncryptFinal_ex(ctx, ciphertext.data() + len, &len))
            handleErrors();
        ciphertext_len += len;

        EVP_CIPHER_CTX_free(ctx);

        ciphertext.resize(ciphertext_len); 
        return ciphertext;
    }

    // Decrypt data
    std::string decrypt(const std::vector<unsigned char>& ciphertext) {
        EVP_CIPHER_CTX* ctx;

        int len;
        int plaintext_len;
        std::vector<unsigned char> plaintext(ciphertext.size());

        if (!(ctx = EVP_CIPHER_CTX_new())) handleErrors();

        if (1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv))
            handleErrors();

        if (1 != EVP_DecryptUpdate(ctx, plaintext.data(), &len, ciphertext.data(), ciphertext.size()))
            handleErrors();
        plaintext_len = len;

        if (1 != EVP_DecryptFinal_ex(ctx, plaintext.data() + len, &len))
            handleErrors();
        plaintext_len += len;

        EVP_CIPHER_CTX_free(ctx);

        plaintext.resize(plaintext_len);
        return std::string(plaintext.begin(), plaintext.end());
    }
};

int main() {
    // Key and IV
    std::string key = "12345678901234567890123456789012"; // 32 bytes
    std::string iv = "1234567890123456"; // 16 bytes

    DataEncryption encryption(key, iv);

    std::string plaintext = "Sensitive cache data that needs encryption";

    // Encrypt
    std::vector<unsigned char> encryptedData = encryption.encrypt(plaintext);
    std::cout << "Encrypted Data: ";
    for (auto byte : encryptedData) {
        std::cout << std::hex << static_cast<int>(byte);
    }
    std::cout << std::endl;

    // Decrypt
    std::string decryptedData = encryption.decrypt(encryptedData);
    std::cout << "Decrypted Data: " << decryptedData << std::endl;

    return 0;
}