#include <iostream>
#include <unordered_map>
#include <vector>
#include <string>
#include <mutex>
#include <thread>
#include <condition_variable>
#include <chrono>
#include "RPCClient.cpp"
#include "MasterSlaveReplication.cpp"
#include "RangePartitioning.cpp"
#include "StrongConsistency.cpp"

class DistributedCache {
private:
    std::unordered_map<std::string, std::string> localCache;
    std::mutex cacheMutex;
    RPCClient rpcClient;
    MasterSlaveReplication replication;
    RangePartitioning partitioning;
    StrongConsistency consistency;

    bool isLeader;
    std::string nodeId;
    std::vector<std::string> peerNodes;

    void replicateData(const std::string& key, const std::string& value) {
        replication.replicate(key, value, peerNodes);
    }

    std::string fetchFromRemote(const std::string& key) {
        std::string partitionNode = partitioning.getNodeForKey(key);
        return rpcClient.get(partitionNode, key);
    }

    bool isKeyLocal(const std::string& key) {
        std::string partitionNode = partitioning.getNodeForKey(key);
        return partitionNode == nodeId;
    }

public:
    DistributedCache(const std::string& nodeId, const std::vector<std::string>& peerNodes, bool isLeader)
        : nodeId(nodeId), peerNodes(peerNodes), isLeader(isLeader) {
    }

    void put(const std::string& key, const std::string& value) {
        std::lock_guard<std::mutex> lock(cacheMutex);

        if (isKeyLocal(key)) {
            localCache[key] = value;
            replicateData(key, value);
            consistency.ensureConsistency(key, value, peerNodes);
        } else {
            std::string partitionNode = partitioning.getNodeForKey(key);
            rpcClient.put(partitionNode, key, value);
        }
    }

    std::string get(const std::string& key) {
        std::lock_guard<std::mutex> lock(cacheMutex);

        if (isKeyLocal(key)) {
            if (localCache.find(key) != localCache.end()) {
                return localCache[key];
            }
        }

        return fetchFromRemote(key);
    }

    void remove(const std::string& key) {
        std::lock_guard<std::mutex> lock(cacheMutex);

        if (isKeyLocal(key)) {
            localCache.erase(key);
            replicateData(key, "");
            consistency.ensureConsistency(key, "", peerNodes);
        } else {
            std::string partitionNode = partitioning.getNodeForKey(key);
            rpcClient.remove(partitionNode, key);
        }
    }

    void promoteToLeader() {
        isLeader = true;
    }

    void handleFailover() {
        std::lock_guard<std::mutex> lock(cacheMutex);
        std::cout << "Handling failover, switching roles." << std::endl;

        if (isLeader) {
            std::cout << "Already a leader, no changes required." << std::endl;
            return;
        }

        promoteToLeader();
    }

    void heartbeatMonitor() {
        while (true) {
            std::this_thread::sleep_for(std::chrono::seconds(10));
            bool allPeersAlive = rpcClient.checkAllPeersAlive(peerNodes);

            if (!allPeersAlive) {
                std::cout << "Detected peer failure. Triggering failover mechanism." << std::endl;
                handleFailover();
            }
        }
    }

    void recoverFromLogs() {
        std::lock_guard<std::mutex> lock(cacheMutex);
        std::cout << "Recovering from logs..." << std::endl;
        // Implement log-based recovery mechanism
    }

    void syncWithPeers() {
        std::lock_guard<std::mutex> lock(cacheMutex);
        std::cout << "Synchronizing with peers..." << std::endl;
        // Synchronization logic to ensure consistent state across nodes
    }

    void printCache() {
        std::lock_guard<std::mutex> lock(cacheMutex);
        std::cout << "Current cache contents:" << std::endl;
        for (const auto& entry : localCache) {
            std::cout << entry.first << " : " << entry.second << std::endl;
        }
    }
};

void simulateNode(DistributedCache& cache) {
    std::thread heartbeatThread(&DistributedCache::heartbeatMonitor, &cache);

    cache.put("key1", "value1");
    cache.put("key2", "value2");
    std::cout << "Get key1: " << cache.get("key1") << std::endl;

    cache.remove("key1");
    std::cout << "Get key1 after removal: " << cache.get("key1") << std::endl;

    cache.printCache();

    heartbeatThread.join();
}

int main() {
    std::vector<std::string> peerNodes = {"node1", "node2", "node3"};
    DistributedCache cache("node1", peerNodes, true);

    simulateNode(cache);

    return 0;
}