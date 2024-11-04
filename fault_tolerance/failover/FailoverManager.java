package fault_tolerance.failover;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

public class FailoverManager {
    private static final Logger logger = Logger.getLogger(FailoverManager.class.getName());
    private final Object membershipService;  
    private final Object raft;              
    private final ExecutorService executorService;
    private final Map<String, String> failedNodes;

    // Native method declarations (for C++ integration via JNI)
    private native void registerHeartbeatFailureCallback();
    private native void sendDataRecoveryRequest(String newNodeId, String failedNodeId);

    static {
        // Load the native libraries
        System.loadLibrary("HeartbeatManager");
        System.loadLibrary("RPCClient");
    }

    public FailoverManager(Object membershipService, Object raft) {
        this.membershipService = membershipService;
        this.raft = raft;
        this.executorService = Executors.newCachedThreadPool();
        this.failedNodes = new HashMap<>();
        initializeFailoverMechanism();
    }

    private void initializeFailoverMechanism() {
        registerHeartbeatFailureCallback();  // Register C++ callback for heartbeat failure
        logger.log(Level.INFO, "Failover mechanism initialized.");
    }

    public void onNodeFailure(String nodeId) {
        executorService.submit(() -> {
            try {
                handleNodeFailure(nodeId);
            } catch (Exception e) {
                logger.log(Level.SEVERE, "Error handling node failure for: " + nodeId, e);
            }
        });
    }

    private void handleNodeFailure(String nodeId) throws Exception {
        logger.log(Level.WARNING, "Node failure detected: " + nodeId);
        if (!failedNodes.containsKey(nodeId)) {
            failedNodes.put(nodeId, "failed");
            attemptFailover(nodeId);
        }
    }

    private void attemptFailover(String nodeId) throws Exception {
        logger.log(Level.INFO, "Attempting failover for node: " + nodeId);
        boolean isLeader = checkIfLeader(); 
        if (isLeader) {
            logger.log(Level.INFO, "Current node is the leader. Initiating failover for: " + nodeId);
            String newNodeId = electNewLeader(nodeId);
            notifyClientsOfFailover(nodeId, newNodeId);
            recoverDataFromReplica(nodeId, newNodeId);
        } else {
            logger.log(Level.INFO, "Current node is not the leader. Awaiting instructions.");
        }
    }

    private boolean checkIfLeader() {
        try {
            // Invoke the `isLeader` method on the Raft object
            return (boolean) raft.getClass().getMethod("isLeader").invoke(raft);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error checking if current node is leader: ", e);
            return false;
        }
    }

    private String electNewLeader(String failedNodeId) throws Exception {
        try {
            // Invoke the `triggerLeaderElection` method on the Raft object
            return (String) raft.getClass().getMethod("triggerLeaderElection").invoke(raft);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error triggering leader election: ", e);
            return null;
        }
    }

    private void notifyClientsOfFailover(String failedNodeId, String newNodeId) {
        logger.log(Level.INFO, "Notifying clients of failover from " + failedNodeId + " to " + newNodeId);

        try {
            // Invoke the `updateNodeStatus` method on the MembershipService object
            membershipService.getClass().getMethod("updateNodeStatus", String.class, String.class)
                    .invoke(membershipService, failedNodeId, "failed");
            membershipService.getClass().getMethod("updateNodeStatus", String.class, String.class)
                    .invoke(membershipService, newNodeId, "active");
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error updating node status: ", e);
        }

        // RPC call handled by C++ (through JNI)
        sendDataRecoveryRequest(newNodeId, failedNodeId);
    }

    private void recoverDataFromReplica(String failedNodeId, String newNodeId) {
        logger.log(Level.INFO, "Recovering data from replica for failed node: " + failedNodeId);
        sendDataRecoveryRequest(newNodeId, failedNodeId);  // JNI call to C++ RPCClient
    }

    public void shutdown() {
        logger.log(Level.INFO, "Shutting down Failover Manager...");
        executorService.shutdown();
        try {
            if (!executorService.awaitTermination(30, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        } catch (InterruptedException e) {
            executorService.shutdownNow();
        }
    }

    public void forceFailover(String nodeId) {
        logger.log(Level.WARNING, "Forcing failover for node: " + nodeId);
        try {
            onNodeFailure(nodeId);
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error during forced failover for: " + nodeId, e);
        }
    }

    // Testing and Diagnostics
    public Map<String, String> getFailedNodes() {
        return new HashMap<>(failedNodes);
    }

    public void resetFailedNodes() {
        failedNodes.clear();
        logger.log(Level.INFO, "Failed nodes list reset.");
    }

    public boolean isNodeFailed(String nodeId) {
        return failedNodes.containsKey(nodeId);
    }

    public static void main(String[] args) {
        // Setup for FailoverManager initialization
        Object membershipService = new Object(); 
        Object raft = new Object();             

        FailoverManager failoverManager = new FailoverManager(membershipService, raft);

        // Simulating a node failure
        failoverManager.forceFailover("node-1");

        // Shutting down the manager
        failoverManager.shutdown();
    }
}