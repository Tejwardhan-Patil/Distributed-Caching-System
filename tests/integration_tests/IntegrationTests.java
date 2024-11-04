package tests.integration_tests;

import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class IntegrationTests {

    @BeforeAll
    public static void setUpEnvironment() throws Exception {
        // Starting all necessary services before running integration tests
        startInMemoryCache();
        startDiskCache();
        startProtobufService();
    }

    @AfterAll
    public static void tearDownEnvironment() throws Exception {
        // Cleaning up after tests
        stopInMemoryCache();
        stopDiskCache();
        stopProtobufService();
    }

    private static void startInMemoryCache() throws Exception {
        // Starting the C++ in-memory cache via system command
        ProcessBuilder processBuilder = new ProcessBuilder("./InMemoryStore", "start");
        processBuilder.start();
    }

    private static void stopInMemoryCache() throws Exception {
        // Stopping the C++ in-memory cache
        ProcessBuilder processBuilder = new ProcessBuilder("./InMemoryStore", "stop");
        processBuilder.start();
    }

    private static void startDiskCache() throws Exception {
        // Starting the Python disk cache
        ProcessBuilder processBuilder = new ProcessBuilder("python3", "DiskStore.py", "start");
        processBuilder.start();
    }

    private static void stopDiskCache() throws Exception {
        // Stopping the Python disk cache
        ProcessBuilder processBuilder = new ProcessBuilder("python3", "DiskStore.py", "stop");
        processBuilder.start();
    }

    private static void startProtobufService() throws Exception {
        // Starting the Java Protobuf Serializer service
        ProcessBuilder processBuilder = new ProcessBuilder("java", "-cp", "ProtobufSerializer.jar", "ProtobufSerializer", "start");
        processBuilder.start();
    }

    private static void stopProtobufService() throws Exception {
        // Stopping the Java Protobuf Serializer service
        ProcessBuilder processBuilder = new ProcessBuilder("java", "-cp", "ProtobufSerializer.jar", "ProtobufSerializer", "stop");
        processBuilder.start();
    }

    @Test
    public void testInMemoryCacheInteraction() throws Exception {
        // Test interaction with the in-memory C++ cache
        ProcessBuilder processBuilder = new ProcessBuilder("./InMemoryStore", "put", "key1", "value1");
        processBuilder.start();
        String result = executeInMemoryCacheCommand("get", "key1");
        assertEquals("value1", result);
    }

    @Test
    public void testDiskCacheFallback() throws Exception {
        // Test interaction between Java and Python DiskStore
        ProcessBuilder processBuilder = new ProcessBuilder("python3", "DiskStore.py", "put", "key2", "value2");
        processBuilder.start();
        String result = executeDiskCacheCommand("get", "key2");
        assertEquals("value2", result);
    }

    private String executeInMemoryCacheCommand(String command, String key) throws Exception {
        ProcessBuilder processBuilder = new ProcessBuilder("./InMemoryStore", command, key);
        Process process = processBuilder.start();
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        return reader.readLine();
    }

    private String executeDiskCacheCommand(String command, String key) throws Exception {
        ProcessBuilder processBuilder = new ProcessBuilder("python3", "DiskStore.py", command, key);
        Process process = processBuilder.start();
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        return reader.readLine();
    }

    @Test
    public void testProtobufSerialization() throws Exception {
        // Testing Protobuf Serializer with Java
        String payload = "{\"key\":\"testKey\", \"value\":\"testValue\"}";
        String serialized = serializeWithProtobuf(payload);
        String deserialized = deserializeWithProtobuf(serialized);

        assertEquals(payload, deserialized);
    }

    private String serializeWithProtobuf(String data) throws Exception {
        URL url = new URL("http://localhost:8080/serialize");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.getOutputStream().write(data.getBytes());

        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        return reader.readLine();
    }

    private String deserializeWithProtobuf(String data) throws Exception {
        URL url = new URL("http://localhost:8080/deserialize");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.getOutputStream().write(data.getBytes());

        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        return reader.readLine();
    }

    @Test
    public void testMultiLanguageIntegration() throws Exception {
        // Testing interaction between components from Java, C++, and Python

        // 1. Insert a value into the C++ in-memory store
        String inMemoryResult = executeInMemoryCacheCommand("put", "multiLangKey");
        assertEquals("OK", inMemoryResult);

        // 2. Retrieve the value from Python DiskStore (simulating a fallback)
        String diskStoreResult = executeDiskCacheCommand("get", "multiLangKey");
        assertEquals("multiLangValue", diskStoreResult);

        // 3. Verify the value is correctly serialized and deserialized by ProtobufSerializer
        String payload = "{\"key\":\"multiLangKey\", \"value\":\"multiLangValue\"}";
        String serialized = serializeWithProtobuf(payload);
        String deserialized = deserializeWithProtobuf(serialized);
        assertEquals(payload, deserialized);
    }
}