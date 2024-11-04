package coordination.membership;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * MembershipService manages the active nodes in a distributed system. 
 * Nodes can join and leave, and the service tracks the state of each node.
 */
public class MembershipService {

    private Set<String> activeNodes; // Active nodes in the system
    private ConcurrentHashMap<String, Long> heartbeatTimestamps; // Tracks the heartbeat timestamps for nodes
    private ScheduledExecutorService heartbeatChecker;
    private static final long HEARTBEAT_TIMEOUT = 5000; // 5 seconds timeout for heartbeats

    public MembershipService() {
        activeNodes = ConcurrentHashMap.newKeySet();
        heartbeatTimestamps = new ConcurrentHashMap<>();
        heartbeatChecker = Executors.newScheduledThreadPool(1);
        startHeartbeatChecker();
    }

    /**
     * Adds a node to the system by generating a unique ID for the node.
     *
     * @return The generated node ID
     */
    public String addNode() {
        String nodeId = UUID.randomUUID().toString();
        activeNodes.add(nodeId);
        updateHeartbeat(nodeId);
        System.out.println("Node added: " + nodeId);
        return nodeId;
    }

    /**
     * Removes a node from the system.
     *
     * @param nodeId The ID of the node to remove
     */
    public void removeNode(String nodeId) {
        activeNodes.remove(nodeId);
        heartbeatTimestamps.remove(nodeId);
        System.out.println("Node removed: " + nodeId);
    }

    /**
     * Updates the heartbeat timestamp for the specified node.
     *
     * @param nodeId The ID of the node to update the heartbeat for
     */
    public void updateHeartbeat(String nodeId) {
        heartbeatTimestamps.put(nodeId, System.currentTimeMillis());
    }

    /**
     * Starts a background process to check the heartbeat of nodes and remove any that have timed out.
     */
    private void startHeartbeatChecker() {
        heartbeatChecker.scheduleAtFixedRate(() -> {
            long currentTime = System.currentTimeMillis();
            for (String nodeId : heartbeatTimestamps.keySet()) {
                long lastHeartbeat = heartbeatTimestamps.get(nodeId);
                if (currentTime - lastHeartbeat > HEARTBEAT_TIMEOUT) {
                    removeNode(nodeId);
                    System.out.println("Node " + nodeId + " timed out due to missing heartbeat.");
                }
            }
        }, 0, HEARTBEAT_TIMEOUT, TimeUnit.MILLISECONDS);
    }

    /**
     * Simulates a heartbeat from a specific node.
     *
     * @param nodeId The ID of the node sending the heartbeat
     */
    public void receiveHeartbeat(String nodeId) {
        if (activeNodes.contains(nodeId)) {
            updateHeartbeat(nodeId);
            System.out.println("Heartbeat received from node: " + nodeId);
        } else {
            System.out.println("Unknown node: " + nodeId);
        }
    }

    /**
     * Shuts down the heartbeat checker service.
     */
    public void shutdown() {
        heartbeatChecker.shutdown();
        try {
            if (!heartbeatChecker.awaitTermination(1, TimeUnit.SECONDS)) {
                heartbeatChecker.shutdownNow();
            }
        } catch (InterruptedException e) {
            heartbeatChecker.shutdownNow();
        }
    }

    /**
     * Returns a set of active nodes in the system.
     *
     * @return A set of active node IDs
     */
    public Set<String> getActiveNodes() {
        return new HashSet<>(activeNodes);
    }

    /**
     * Simulates a failure detection test for the MembershipService.
     */
    public static void main(String[] args) throws InterruptedException {
        MembershipService membershipService = new MembershipService();

        // Simulating node join
        String node1 = membershipService.addNode();
        String node2 = membershipService.addNode();
        
        // Simulating heartbeats
        membershipService.receiveHeartbeat(node1);
        membershipService.receiveHeartbeat(node2);
        
        // Simulating a delay for heartbeat timeout
        Thread.sleep(6000);
        
        // Node 2's heartbeat will time out
        membershipService.receiveHeartbeat(node1);
        
        // Shutdown the membership service
        membershipService.shutdown();
        
        System.out.println("Active nodes: " + membershipService.getActiveNodes());
    }
}