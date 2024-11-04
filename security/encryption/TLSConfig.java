package security.encryption;

import java.io.FileInputStream;
import java.security.KeyStore;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManagerFactory;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLSocket;
import java.net.Socket;
import java.io.OutputStream;
import java.io.InputStream;
import java.util.Arrays;

public class TLSConfig {
    
    private static final String PROTOCOL = "TLS";
    private static final String KEY_STORE_TYPE = "PKCS12";
    private static final String TRUST_STORE_TYPE = "JKS";
    private static final String KEY_MANAGER_ALGORITHM = "SunX509";
    private static final String TRUST_MANAGER_ALGORITHM = "SunX509";
    private static final String CIPHER_SUITES[] = { 
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384", 
        "TLS_RSA_WITH_AES_256_CBC_SHA256"
    };

    private String keyStoreFile;
    private String trustStoreFile;
    private String keyStorePassword;
    private String trustStorePassword;
    
    public TLSConfig(String keyStoreFile, String trustStoreFile, String keyStorePassword, String trustStorePassword) {
        this.keyStoreFile = keyStoreFile;
        this.trustStoreFile = trustStoreFile;
        this.keyStorePassword = keyStorePassword;
        this.trustStorePassword = trustStorePassword;
    }
    
    public SSLSocketFactory createSSLSocketFactory() throws Exception {
        // Load KeyStore
        KeyStore keyStore = KeyStore.getInstance(KEY_STORE_TYPE);
        try (FileInputStream keyStoreStream = new FileInputStream(keyStoreFile)) {
            keyStore.load(keyStoreStream, keyStorePassword.toCharArray());
        }
        
        // Initialize KeyManagerFactory with KeyStore
        KeyManagerFactory keyManagerFactory = KeyManagerFactory.getInstance(KEY_MANAGER_ALGORITHM);
        keyManagerFactory.init(keyStore, keyStorePassword.toCharArray());
        
        // Load TrustStore
        KeyStore trustStore = KeyStore.getInstance(TRUST_STORE_TYPE);
        try (FileInputStream trustStoreStream = new FileInputStream(trustStoreFile)) {
            trustStore.load(trustStoreStream, trustStorePassword.toCharArray());
        }

        // Initialize TrustManagerFactory with TrustStore
        TrustManagerFactory trustManagerFactory = TrustManagerFactory.getInstance(TRUST_MANAGER_ALGORITHM);
        trustManagerFactory.init(trustStore);
        
        // Set up SSL context with the loaded key and trust managers
        SSLContext sslContext = SSLContext.getInstance(PROTOCOL);
        sslContext.init(keyManagerFactory.getKeyManagers(), trustManagerFactory.getTrustManagers(), null);
        
        // Return the SSLSocketFactory
        return sslContext.getSocketFactory();
    }

    public void configureTLSSocket(Socket socket) throws Exception {
        if (socket instanceof SSLSocket) {
            SSLSocket sslSocket = (SSLSocket) socket;
            sslSocket.setEnabledCipherSuites(CIPHER_SUITES);
            sslSocket.startHandshake();
        }
    }
    
    public static void main(String[] args) {
        try {
            String keyStorePath = "/keystore.p12";
            String trustStorePath = "/truststore.jks";
            String keyStorePassword = "keystore_password";
            String trustStorePassword = "truststore_password";

            TLSConfig tlsConfig = new TLSConfig(keyStorePath, trustStorePath, keyStorePassword, trustStorePassword);
            SSLSocketFactory sslSocketFactory = tlsConfig.createSSLSocketFactory();
            
            // Create SSL Socket to server 
            Socket socket = sslSocketFactory.createSocket("website.com", 443);
            tlsConfig.configureTLSSocket(socket);
            
            // Communication with the server
            try (OutputStream out = socket.getOutputStream();
                 InputStream in = socket.getInputStream()) {
                // Send and receive data over the secure socket
                String request = "GET / HTTP/1.1\r\nHost: website.com\r\n\r\n";
                out.write(request.getBytes());
                out.flush();
                
                byte[] response = new byte[4096];
                int bytesRead = in.read(response);
                System.out.println("Response: " + new String(response, 0, bytesRead));
            }

            socket.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}