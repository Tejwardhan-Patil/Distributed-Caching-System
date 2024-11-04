package distributed.sharding;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import distributed.partitioning.ConsistentHashing;
import distributed.replication.ReplicationStrategy;
import distributed.replication.Replica;
import networking.rpc.RPCServer;
import networking.rpc.RPCClient;

public class ShardManager<T> {

    private final ConsistentHashing<T> consistentHashing;
    private final ReplicationStrategy replicationStrategy;
    private final Map<String, T> shardMap; // Maps shard ID to node
    private final Set<T> activeNodes; // Nodes currently active
    private final ConcurrentHashMap<String, List<Replica>> replicaMap; // Replica management
    private final RPCServer rpcServer;
    private final RPCClient rpcClient;
    private final int replicationFactor;

    public ShardManager(ConsistentHashing<T> consistentHashing, ReplicationStrategy replicationStrategy, 
                        RPCServer rpcServer, RPCClient rpcClient, int replicationFactor) {
        this.consistentHashing = consistentHashing;
        this.replicationStrategy = replicationStrategy;
        this.replicationFactor = replicationFactor;
        this.shardMap = new ConcurrentHashMap<>();
        this.activeNodes = new HashSet<>();
        this.replicaMap = new ConcurrentHashMap<>();
        this.rpcServer = rpcServer;
        this.rpcClient = rpcClient;
    }

    // Adds a new node to the shard management system
    public void addNode(T node) {
        consistentHashing.addNode(node);
        activeNodes.add(node);
        rebalanceShards();
    }

    // Removes a node from the shard management system
    public void removeNode(T node) {
        consistentHashing.removeNode(node);
        activeNodes.remove(node);
        rebalanceShards();
    }

    // Allocates or rebalances shards after nodes are added or removed
    private void rebalanceShards() {
        shardMap.clear();
        for (String shardId : shardMap.keySet()) {
            T node = consistentHashing.getNodeForKey(shardId); 
            shardMap.put(shardId, node);
        }
        manageReplicas();
    }

    // Manages replica placement for shards
    private void manageReplicas() {
        replicaMap.clear();
        for (String shardId : shardMap.keySet()) {
            T primaryNode = shardMap.get(shardId);
            List<T> replicas = replicationStrategy.getReplicas(primaryNode, replicationFactor);
            List<Replica> replicaList = new ArrayList<>();
            for (T replica : replicas) {
                replicaList.add(new Replica(replica));
            }
            replicaMap.put(shardId, replicaList);
        }
    }

    // Retrieves the node responsible for a given shard ID
    public T getNodeForShard(String shardId) {
        return shardMap.getOrDefault(shardId, consistentHashing.getNodeForKey(shardId)); 
    }

    // Returns the replica list for a specific shard
    public List<Replica> getReplicasForShard(String shardId) {
        return replicaMap.get(shardId);
    }

    // Handles failure of a node by reassigning its shards
    public void handleNodeFailure(T failedNode) {
        activeNodes.remove(failedNode);
        consistentHashing.removeNode(failedNode);
        rebalanceShards();
    }

    // Adds a shard to the shard manager
    public void addShard(String shardId) {
        T node = consistentHashing.getNodeForKey(shardId);
        shardMap.put(shardId, node);
        manageReplicas();
    }

    // Removes a shard from the shard manager
    public void removeShard(String shardId) {
        shardMap.remove(shardId);
        replicaMap.remove(shardId);
    }

    // Fetches all active nodes in the system
    public Set<T> getActiveNodes() {
        return Collections.unmodifiableSet(activeNodes);
    }

    // Handles RPC request to get the responsible node for a shard
    public void handleShardRequest(String shardId) {
        T node = getNodeForShard(shardId);
        rpcServer.sendResponse(node);
    }
}