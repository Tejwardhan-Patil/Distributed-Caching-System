#include <iostream>
#include <vector>
#include <map>
#include <algorithm>
#include <stdexcept>

class Node {
public:
    std::string nodeId;
    std::string ipAddress;
    int port;

    Node(std::string nodeId, std::string ipAddress, int port)
        : nodeId(nodeId), ipAddress(ipAddress), port(port) {}

    void displayInfo() const {
        std::cout << "Node ID: " << nodeId << ", IP Address: " << ipAddress << ", Port: " << port << std::endl;
    }
};

class RangePartition {
public:
    int startRange;
    int endRange;
    Node node;

    RangePartition(int startRange, int endRange, Node node)
        : startRange(startRange), endRange(endRange), node(node) {}

    bool isInRange(int key) const {
        return key >= startRange && key <= endRange;
    }
};

class RangePartitioning {
private:
    std::vector<RangePartition> partitions;

public:
    RangePartitioning() = default;

    void addPartition(int startRange, int endRange, const Node& node) {
        if (startRange >= endRange) {
            throw std::invalid_argument("Start range must be less than end range.");
        }
        partitions.emplace_back(startRange, endRange, node);
    }

    Node findNodeForKey(int key) const {
        for (const auto& partition : partitions) {
            if (partition.isInRange(key)) {
                return partition.node;
            }
        }
        throw std::out_of_range("Key out of range of all partitions.");
    }

    void displayPartitions() const {
        for (const auto& partition : partitions) {
            std::cout << "Range: [" << partition.startRange << "-" << partition.endRange << "] ";
            partition.node.displayInfo();
        }
    }
};

// Simulate a distributed cache operation that interacts with partitioned nodes
class DistributedCache {
private:
    RangePartitioning partitioning;

public:
    DistributedCache(const RangePartitioning& partitioning)
        : partitioning(partitioning) {}

    void put(int key, const std::string& value) {
        try {
            Node node = partitioning.findNodeForKey(key);
            std::cout << "Storing key " << key << " with value '" << value << "' on node " << node.nodeId << std::endl;
        } catch (const std::out_of_range& e) {
            std::cerr << e.what() << std::endl;
        }
    }

    void get(int key) {
        try {
            Node node = partitioning.findNodeForKey(key);
            std::cout << "Fetching key " << key << " from node " << node.nodeId << std::endl;
        } catch (const std::out_of_range& e) {
            std::cerr << e.what() << std::endl;
        }
    }
};

// Usage
int main() {
    Node node1("Node1", "192.168.1.1", 8080);
    Node node2("Node2", "192.168.1.2", 8080);
    Node node3("Node3", "192.168.1.3", 8080);

    RangePartitioning partitioning;
    partitioning.addPartition(0, 99, node1);
    partitioning.addPartition(100, 199, node2);
    partitioning.addPartition(200, 299, node3);

    partitioning.displayPartitions();

    DistributedCache cache(partitioning);

    cache.put(50, "Value1");
    cache.put(150, "Value2");
    cache.put(250, "Value3");
    cache.get(50);
    cache.get(150);
    cache.get(250);

    return 0;
}