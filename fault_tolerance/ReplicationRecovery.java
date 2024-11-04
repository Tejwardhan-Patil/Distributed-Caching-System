package fault_tolerance;

import distributed.partitioning.ConsistentHashing;
import distributed.replication.ReplicationStrategy;
import networking.rpc.RPCServer;
import monitoring.logging.LogConfig;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.logging.Logger;
import java.util.concurrent.ConcurrentHashMap;

public class ReplicationRecovery {

    static {
        // Load the native C++ library for RPCClient
        System.loadLibrary("rpcclient"); 
    }

    // Native method declarations for interacting with the C++ RPCClient
    private native String sendRequestToNode(String node, String operation, String key, String value);
    private native String sendHeartbeat(String node);

    private static final Logger logger = LogConfig.getLogger(ReplicationRecovery.class);
    private final ConsistentHashing<String> consistentHashing; // Parameterized to use String for node identifiers and keys
    private final ReplicationStrategy replicationStrategy;
    private final RPCServer rpcServer;
    private final Map<String, String> cacheData;
    private final Map<String, String> replicaData;
    private final Map<String, Boolean> recoveryStatus;

    public ReplicationRecovery(ConsistentHashing<String> consistentHashing, ReplicationStrategy replicationStrategy, RPCServer rpcServer) {
        this.consistentHashing = consistentHashing;
        this.replicationStrategy = replicationStrategy;
        this.rpcServer = rpcServer;
        this.cacheData = new ConcurrentHashMap<>();
        this.replicaData = new ConcurrentHashMap<>();
        this.recoveryStatus = new ConcurrentHashMap<>();
    }

    public void initialize() {
        logger.info("Initializing Replication Recovery");
        rpcServer.registerHandler("recoverData", this::handleRecoveryRequest);
        rpcServer.registerHandler("fetchReplicaData", this::handleFetchReplicaData);
    }

    public void addDataToCache(String key, String value) {
        cacheData.put(key, value);
        replicateData(key, value);
    }

    private void replicateData(String key, String value) {
        List<String> replicas = replicationStrategy.getReplicas(key);
        for (String replica : replicas) {
            try {
                sendRequestToNode(replica, "storeReplicaData", key, value);
                logger.info("Replicated data to " + replica);
            } catch (Exception e) {
                logger.severe("Failed to replicate data to " + replica + ": " + e.getMessage());
            }
        }
    }

    public void removeDataFromCache(String key) {
        cacheData.remove(key);
        removeReplicaData(key);
    }

    private void removeReplicaData(String key) {
        List<String> replicas = replicationStrategy.getReplicas(key);
        for (String replica : replicas) {
            try {
                sendRequestToNode(replica, "deleteReplicaData", key, null);
                logger.info("Removed replica data from " + replica);
            } catch (Exception e) {
                logger.severe("Failed to remove replica data from " + replica + ": " + e.getMessage());
            }
        }
    }

    public void recoverLostData(String failedNode) {
        logger.info("Starting recovery process for failed node: " + failedNode);
        List<String> affectedKeys = consistentHashing.getKeysOnNode(failedNode);
        for (String key : affectedKeys) {
            if (recoveryStatus.containsKey(key) && recoveryStatus.get(key)) {
                logger.info("Data already recovered for key: " + key);
                continue;
            }
            try {
                String replicaNode = replicationStrategy.getPrimaryReplica(key);
                String recoveredData = sendRequestToNode(replicaNode, "fetchReplicaData", key, null);
                cacheData.put(key, recoveredData);
                recoveryStatus.put(key, true);
                logger.info("Recovered data for key: " + key + " from replica: " + replicaNode);
            } catch (Exception e) {
                logger.severe("Failed to recover data for key: " + key + ": " + e.getMessage());
                recoveryStatus.put(key, false);
            }
        }
    }

    private Object handleRecoveryRequest(Object[] args) {
        String failedNode = (String) args[0];
        recoverLostData(failedNode);
        return "Recovery Process Completed for node: " + failedNode;
    }

    private Object handleFetchReplicaData(Object[] args) {
        String key = (String) args[0];
        if (replicaData.containsKey(key)) {
            return replicaData.get(key);
        }
        return null;
    }

    public void storeReplicaData(String key, String value) {
        replicaData.put(key, value);
        logger.info("Stored replica data for key: " + key);
    }

    public void deleteReplicaData(String key) {
        replicaData.remove(key);
        logger.info("Deleted replica data for key: " + key);
    }

    public Map<String, String> getCacheData() {
        return cacheData;
    }

    public Map<String, String> getReplicaData() {
        return replicaData;
    }

    public void triggerRecoveryOnFailure(String failedNode) {
        new Thread(() -> recoverLostData(failedNode)).start();
    }

    public void monitorNodes() {
        logger.info("Monitoring node failures");
        List<String> nodes = consistentHashing.getAllNodes();
        for (String node : nodes) {
            if (!isNodeAlive(node)) {
                logger.warning("Detected failure in node: " + node);
                triggerRecoveryOnFailure(node);
            }
        }
    }

    private boolean isNodeAlive(String node) {
        try {
            String response = sendHeartbeat(node);
            return response != null && response.equals("alive");
        } catch (Exception e) {
            return false;
        }
    }

    public void shutDown() {
        logger.info("Shutting down Replication Recovery");
        rpcServer.stop();
    }

    public static void main(String[] args) {
        ConsistentHashing<String> consistentHashing = new ConsistentHashing<>();
        ReplicationStrategy replicationStrategy = new ReplicationStrategy();
        RPCServer rpcServer = new RPCServer();

        ReplicationRecovery replicationRecovery = new ReplicationRecovery(consistentHashing, replicationStrategy, rpcServer);
        replicationRecovery.initialize();

        replicationRecovery.addDataToCache("key1", "value1");
        replicationRecovery.addDataToCache("key2", "value2");

        replicationRecovery.triggerRecoveryOnFailure("node1");

        replicationRecovery.shutDown();
    }
}