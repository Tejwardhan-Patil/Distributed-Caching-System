package distributed.replication;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Base class for replication strategies in a distributed system.
 * Defines the interface and common utilities for replication strategies.
 */
public abstract class ReplicationStrategy {

    // Map of nodes and their data
    protected Map<String, List<String>> nodeDataMap;
    
    // Lock for thread-safe operations
    private ReentrantLock lock;

    /**
     * Constructor initializes the node data map and the lock.
     */
    public ReplicationStrategy() {
        this.nodeDataMap = new HashMap<>();
        this.lock = new ReentrantLock();
    }

    /**
     * Abstract method to define the replication logic.
     * @param nodeID The node where the write operation originated.
     * @param data The data to replicate.
     */
    public abstract void replicate(String nodeID, String data);

    /**
     * Adds data to the node's data list.
     * @param nodeID The ID of the node where the data is stored.
     * @param data The data to be stored.
     */
    protected void addDataToNode(String nodeID, String data) {
        lock.lock();
        try {
            nodeDataMap.computeIfAbsent(nodeID, k -> new java.util.ArrayList<>()).add(data);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Retrieves data from a node.
     * @param nodeID The ID of the node from which to retrieve data.
     * @return The list of data stored on the node.
     */
    public List<String> getNodeData(String nodeID) {
        lock.lock();
        try {
            return nodeDataMap.getOrDefault(nodeID, java.util.Collections.emptyList());
        } finally {
            lock.unlock();
        }
    }

    /**
     * Gets all nodes in the replication group.
     * @return The list of node IDs.
     */
    public List<String> getAllNodes() {
        lock.lock();
        try {
            return new java.util.ArrayList<>(nodeDataMap.keySet());
        } finally {
            lock.unlock();
        }
    }

    /**
     * Removes a node from the replication group.
     * @param nodeID The ID of the node to remove.
     */
    public void removeNode(String nodeID) {
        lock.lock();
        try {
            nodeDataMap.remove(nodeID);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Abstract method to define node failure recovery.
     * @param nodeID The ID of the node that has failed.
     */
    public abstract void recoverFromFailure(String nodeID);

    /**
     * Clears all data from the replication strategy.
     */
    public void clearAllData() {
        lock.lock();
        try {
            nodeDataMap.clear();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Prints the current data stored on each node.
     */
    public void printData() {
        lock.lock();
        try {
            for (Map.Entry<String, List<String>> entry : nodeDataMap.entrySet()) {
                System.out.println("Node: " + entry.getKey() + " Data: " + entry.getValue());
            }
        } finally {
            lock.unlock();
        }
    }
}

/**
 * Implementation of the Master-Slave replication strategy.
 */
class MasterSlaveReplication extends ReplicationStrategy {

    private String masterNodeID;

    /**
     * Constructor for Master-Slave Replication strategy.
     * @param masterNodeID The node ID of the master node.
     */
    public MasterSlaveReplication(String masterNodeID) {
        this.masterNodeID = masterNodeID;
    }

    /**
     * Replicates data from master node to all other nodes.
     * @param nodeID The node where the write operation originated.
     * @param data The data to replicate.
     */
    @Override
    public void replicate(String nodeID, String data) {
        if (nodeID.equals(masterNodeID)) {
            addDataToNode(masterNodeID, data);
            for (String node : getAllNodes()) {
                if (!node.equals(masterNodeID)) {
                    addDataToNode(node, data);
                }
            }
            System.out.println("Data replicated to all slaves from master: " + masterNodeID);
        } else {
            System.out.println("Write denied. Only master node " + masterNodeID + " can accept writes.");
        }
    }

    /**
     * Recovers data from the master node in case of failure.
     * @param nodeID The ID of the node that has failed.
     */
    @Override
    public void recoverFromFailure(String nodeID) {
        if (!nodeID.equals(masterNodeID)) {
            List<String> masterData = getNodeData(masterNodeID);
            addDataToNode(nodeID, String.join(",", masterData));
            System.out.println("Node " + nodeID + " recovered from master.");
        } else {
            System.out.println("Master node has failed! Manual intervention needed.");
        }
    }

    /**
     * Prints the current master node.
     */
    public void printMasterNode() {
        System.out.println("Current master node is: " + masterNodeID);
    }
}

/**
 * Implementation of Multi-Master replication strategy.
 */
class MultiMasterReplication extends ReplicationStrategy {

    /**
     * Replicates data across all master nodes.
     * @param nodeID The node where the write operation originated.
     * @param data The data to replicate.
     */
    @Override
    public void replicate(String nodeID, String data) {
        addDataToNode(nodeID, data);
        for (String node : getAllNodes()) {
            if (!node.equals(nodeID)) {
                addDataToNode(node, data);
            }
        }
        System.out.println("Data replicated across all masters.");
    }

    /**
     * Recovers data from a surviving node in case of failure.
     * @param nodeID The ID of the node that has failed.
     */
    @Override
    public void recoverFromFailure(String nodeID) {
        for (String node : getAllNodes()) {
            if (!node.equals(nodeID)) {
                List<String> survivingNodeData = getNodeData(node);
                addDataToNode(nodeID, String.join(",", survivingNodeData));
                System.out.println("Node " + nodeID + " recovered from surviving node " + node);
                return;
            }
        }
    }
}