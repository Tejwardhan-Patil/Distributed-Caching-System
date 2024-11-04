package networking.protocols;

import org.apache.thrift.TException;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;
import org.apache.thrift.server.TServer;
import org.apache.thrift.server.TSimpleServer;
import org.apache.thrift.transport.TServerSocket;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TTransport;
import org.apache.thrift.transport.TTransportException;
import org.apache.thrift.transport.TServerTransport;
import org.apache.thrift.transport.TTransportFactory;
import org.apache.thrift.transport.TFramedTransport;
import org.apache.thrift.transport.TNonblockingServerSocket;
import org.apache.thrift.server.TNonblockingServer;
import org.apache.thrift.server.TThreadPoolServer;

import java.util.HashMap;
import java.util.Map;

// ThriftProtocol implementation for lightweight communication between nodes in the distributed system

public class ThriftProtocol {
    
    // The cache store which will hold the cached data in memory
    private static Map<String, String> cacheStore = new HashMap<>();

    // The service interface implemented by the cache service
    public static class CacheServiceHandler implements CacheService.Iface {

        @Override
        public String get(String key) throws TException {
            if (cacheStore.containsKey(key)) {
                System.out.println("Cache hit: " + key);
                return cacheStore.get(key);
            } else {
                System.out.println("Cache miss: " + key);
                return null;
            }
        }

        @Override
        public void put(String key, String value) throws TException {
            System.out.println("Adding to cache: " + key + " -> " + value);
            cacheStore.put(key, value);
        }

        @Override
        public boolean delete(String key) throws TException {
            if (cacheStore.containsKey(key)) {
                cacheStore.remove(key);
                System.out.println("Deleted from cache: " + key);
                return true;
            }
            return false;
        }
    }

    // Method to start a simple blocking Thrift server
    public static void startSimpleServer(CacheService.Processor<CacheServiceHandler> processor) {
        try {
            TServerTransport serverTransport = new TServerSocket(9090);
            TServer server = new TSimpleServer(new TServer.Args(serverTransport).processor(processor));

            System.out.println("Starting the simple Thrift server on port 9090...");
            server.serve();
        } catch (TTransportException e) {
            e.printStackTrace();
        }
    }

    // Method to start a thread pool server
    public static void startThreadPoolServer(CacheService.Processor<CacheServiceHandler> processor) {
        try {
            TServerTransport serverTransport = new TServerSocket(9090);
            TTransportFactory transportFactory = new TFramedTransport.Factory();
            TServer server = new TThreadPoolServer(new TThreadPoolServer.Args(serverTransport)
                .processor(processor).transportFactory(transportFactory));

            System.out.println("Starting the thread pool Thrift server on port 9090...");
            server.serve();
        } catch (TTransportException e) {
            e.printStackTrace();
        }
    }

    // Method to start a non-blocking Thrift server
    public static void startNonBlockingServer(CacheService.Processor<CacheServiceHandler> processor) {
        try {
            TNonblockingServerSocket serverTransport = new TNonblockingServerSocket(9090);
            TServer server = new TNonblockingServer(new TNonblockingServer.Args(serverTransport).processor(processor));

            System.out.println("Starting the non-blocking Thrift server on port 9090...");
            server.serve();
        } catch (TTransportException e) {
            e.printStackTrace();
        }
    }

    // Method to start a client connection to the Thrift server
    public static void startClient(String host, int port) {
        try {
            TTransport transport = new TSocket(host, port);
            transport.open();

            TProtocol protocol = new TBinaryProtocol(transport);
            CacheService.Client client = new CacheService.Client(protocol);

            // Sample operations on the cache
            client.put("key1", "value1");
            System.out.println("Put key1 -> value1");

            String result = client.get("key1");
            System.out.println("Get key1: " + result);

            boolean deleted = client.delete("key1");
            System.out.println("Deleted key1: " + deleted);

            transport.close();
        } catch (TException x) {
            x.printStackTrace();
        }
    }

    // Main method to demonstrate the server and client operations
    public static void main(String[] args) {
        try {
            CacheServiceHandler handler = new CacheServiceHandler();
            CacheService.Processor<CacheServiceHandler> processor = new CacheService.Processor<>(handler);

            // Start the Thrift server in a new thread
            Runnable simpleServer = new Runnable() {
                public void run() {
                    startSimpleServer(processor);
                }
            };
            new Thread(simpleServer).start();

            // Allow time for the server to start
            Thread.sleep(1000);

            // Start the client
            startClient("localhost", 9090);

        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}