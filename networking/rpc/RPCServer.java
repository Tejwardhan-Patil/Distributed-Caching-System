package networking.rpc;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.HashMap;
import java.util.Map;

public class RPCServer {

    private static final Logger logger = Logger.getLogger(RPCServer.class.getName());
    private int port;
    private boolean running;
    private ServerSocket serverSocket;
    private ExecutorService threadPool;
    private Map<String, RPCHandler> handlers;

    public RPCServer(int port, int threadPoolSize) {
        this.port = port;
        this.threadPool = Executors.newFixedThreadPool(threadPoolSize);
        this.handlers = new HashMap<>();
    }

    public void start() {
        try {
            serverSocket = new ServerSocket(port);
            running = true;
            logger.info("RPC Server started on port " + port);

            while (running) {
                Socket clientSocket = serverSocket.accept();
                threadPool.execute(new ClientHandler(clientSocket));
            }
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error starting RPC Server", e);
        }
    }

    public void stop() {
        running = false;
        threadPool.shutdown();
        try {
            serverSocket.close();
            logger.info("RPC Server stopped.");
        } catch (IOException e) {
            logger.log(Level.SEVERE, "Error stopping RPC Server", e);
        }
    }

    public void registerHandler(String methodName, RPCHandler handler) {
        handlers.put(methodName, handler);
    }

    private class ClientHandler implements Runnable {
        private Socket clientSocket;

        public ClientHandler(Socket clientSocket) {
            this.clientSocket = clientSocket;
        }

        @Override
        public void run() {
            try (ObjectInputStream input = new ObjectInputStream(clientSocket.getInputStream());
                 ObjectOutputStream output = new ObjectOutputStream(clientSocket.getOutputStream())) {

                String methodName = input.readUTF();
                Object[] params = (Object[]) input.readObject();
                logger.info("Received request for method: " + methodName);

                if (handlers.containsKey(methodName)) {
                    Object result = handlers.get(methodName).handle(params);
                    output.writeObject(result);
                } else {
                    output.writeObject(new RPCError("Method not found: " + methodName));
                }

                output.flush();
            } catch (IOException | ClassNotFoundException e) {
                logger.log(Level.SEVERE, "Error handling client request", e);
            } finally {
                try {
                    clientSocket.close();
                } catch (IOException e) {
                    logger.log(Level.SEVERE, "Error closing client socket", e);
                }
            }
        }
    }

    public static void main(String[] args) {
        RPCServer server = new RPCServer(8080, 10);
        server.registerHandler("add", new AddHandler());
        server.registerHandler("subtract", new SubtractHandler());
        server.start();
    }
}

interface RPCHandler {
    Object handle(Object[] params);
}

class AddHandler implements RPCHandler {
    @Override
    public Object handle(Object[] params) {
        int a = (int) params[0];
        int b = (int) params[1];
        return a + b;
    }
}

class SubtractHandler implements RPCHandler {
    @Override
    public Object handle(Object[] params) {
        int a = (int) params[0];
        int b = (int) params[1];
        return a - b;
    }
}

class RPCError {
    private String message;

    public RPCError(String message) {
        this.message = message;
    }

    public String getMessage() {
        return message;
    }
}