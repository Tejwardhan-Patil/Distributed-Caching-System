package monitoring.logging;

import java.io.IOException;
import java.util.logging.ConsoleHandler;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;
import java.util.logging.XMLFormatter;
import java.util.logging.Handler;
import java.util.logging.StreamHandler;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class LogConfig {

    private static Logger logger = Logger.getLogger(LogConfig.class.getName());

    private static FileHandler fileHandler;
    private static ConsoleHandler consoleHandler;
    private static Handler cloudHandler;

    // Enum to handle log levels
    public enum LogLevel {
        INFO(Level.INFO),
        WARNING(Level.WARNING),
        SEVERE(Level.SEVERE),
        CONFIG(Level.CONFIG),
        FINE(Level.FINE),
        FINER(Level.FINER),
        FINEST(Level.FINEST);

        private Level level;

        LogLevel(Level level) {
            this.level = level;
        }

        public Level getLevel() {
            return this.level;
        }
    }

    // Initialize logging configuration
    public static void initializeLogging(String outputType, String logFilePath, LogLevel logLevel, String cloudEndpoint) {
        try {
            // Set log level for logger
            logger.setLevel(logLevel.getLevel());

            switch (outputType.toLowerCase()) {
                case "file":
                    setupFileLogging(logFilePath);
                    break;
                case "console":
                    setupConsoleLogging();
                    break;
                case "cloud":
                    setupCloudLogging(cloudEndpoint);
                    break;
                default:
                    logger.warning("Invalid output type. Defaulting to console logging.");
                    setupConsoleLogging();
                    break;
            }
        } catch (IOException e) {
            logger.severe("Failed to initialize logging: " + e.getMessage());
        }
    }

    // Setup logging to file
    private static void setupFileLogging(String logFilePath) throws IOException {
        fileHandler = new FileHandler(logFilePath, true); // append mode
        fileHandler.setFormatter(new SimpleFormatter());
        logger.addHandler(fileHandler);
        logger.info("File logging initialized. Log file: " + logFilePath);
    }

    // Setup logging to console
    private static void setupConsoleLogging() {
        consoleHandler = new ConsoleHandler();
        consoleHandler.setLevel(logger.getLevel());
        consoleHandler.setFormatter(new SimpleFormatter());
        logger.addHandler(consoleHandler);
        logger.info("Console logging initialized.");
    }

    // Setup cloud logging to an HTTP endpoint
    private static void setupCloudLogging(final String cloudEndpoint) {
        cloudHandler = new StreamHandler() {
            @Override
            public void publish(java.util.logging.LogRecord record) {
                try {
                    URL url = new URL(cloudEndpoint);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setDoOutput(true);
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");

                    String logMessage = "{\"level\": \"" + record.getLevel() + "\", \"message\": \"" + record.getMessage() + "\"}";
                    byte[] input = logMessage.getBytes(StandardCharsets.UTF_8);

                    OutputStream os = conn.getOutputStream();
                    os.write(input, 0, input.length);

                    int responseCode = conn.getResponseCode();
                    if (responseCode != 200) {
                        logger.warning("Failed to send log to cloud. Response code: " + responseCode);
                    }
                    os.flush();
                    os.close();
                } catch (IOException e) {
                    logger.severe("Error sending log to cloud: " + e.getMessage());
                }
            }
        };
        logger.addHandler(cloudHandler);
        logger.info("Cloud logging initialized with endpoint: " + cloudEndpoint);
    }

    // Method to change log level dynamically
    public static void setLogLevel(LogLevel newLogLevel) {
        logger.setLevel(newLogLevel.getLevel());
        logger.info("Log level changed to: " + newLogLevel);
    }

    // Clean up handlers before application shutdown
    public static void cleanup() {
        if (fileHandler != null) {
            fileHandler.close();
        }
        if (consoleHandler != null) {
            consoleHandler.close();
        }
        if (cloudHandler != null) {
            cloudHandler.close();
        }
    }

    // Test log output
    public static void testLogging() {
        logger.info("This is an INFO message");
        logger.warning("This is a WARNING message");
        logger.severe("This is a SEVERE message");
    }

    // Advanced logging to handle XML format (for structured logs)
    public static void setupXMLLogging(String logFilePath) throws IOException {
        fileHandler = new FileHandler(logFilePath, true);
        fileHandler.setFormatter(new XMLFormatter());
        logger.addHandler(fileHandler);
        logger.info("XML logging initialized. Log file: " + logFilePath);
    }

    public static void main(String[] args) {
        // Initialize logging to a file with INFO level
        String cloudEndpoint = "https://website.com/log-endpoint";
        initializeLogging("cloud", "logs/application.log", LogLevel.INFO, cloudEndpoint);

        // Testing log messages
        testLogging();

        // Changing log level at runtime
        setLogLevel(LogLevel.FINE);
        logger.fine("This is a FINE log message");

        // Clean up before exiting
        cleanup();
    }
}