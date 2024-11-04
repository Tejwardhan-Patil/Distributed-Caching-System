#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <thread>
#include <condition_variable>
#include <chrono>

class SlaveNode {
public:
    SlaveNode(int id) : nodeId(id), dataVersion(0) {}

    void updateData(const std::string &newData, int version) {
        std::unique_lock<std::mutex> lock(mtx);
        data = newData;
        dataVersion = version;
        std::cout << "Slave " << nodeId << " updated to version " << version << ": " << data << std::endl;
    }

    int getVersion() const {
        return dataVersion;
    }

private:
    int nodeId;
    int dataVersion;
    std::string data;
    mutable std::mutex mtx;
};

class MasterNode {
public:
    MasterNode() : version(0) {}

    void addSlave(SlaveNode* slave) {
        slaves.push_back(slave);
    }

    void updateData(const std::string &newData) {
        {
            std::lock_guard<std::mutex> lock(mtx);
            version++;
            data = newData;
            std::cout << "Master updated to version " << version << ": " << data << std::endl;
        }
        replicateToSlaves();
    }

    void replicateToSlaves() {
        for (auto &slave : slaves) {
            std::thread replicationThread(&MasterNode::replicate, this, slave);
            replicationThread.detach();
        }
    }

    void replicate(SlaveNode* slave) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Simulating network delay
        if (slave->getVersion() < version) {
            slave->updateData(data, version);
        }
    }

    void manualFailover(int failedSlaveId) {
        std::cout << "Failover initiated for Slave " << failedSlaveId << std::endl;
        for (auto &slave : slaves) {
            if (slave->getVersion() < version) {
                std::thread failoverThread(&MasterNode::replicate, this, slave);
                failoverThread.detach();
            }
        }
    }

private:
    int version;
    std::string data;
    std::vector<SlaveNode*> slaves;
    std::mutex mtx;
};

class HealthChecker {
public:
    HealthChecker(MasterNode &master, std::vector<SlaveNode*> slaves)
        : masterNode(master), slaveNodes(slaves), isRunning(true) {}

    void start() {
        std::thread checker(&HealthChecker::monitor, this);
        checker.detach();
    }

    void stop() {
        isRunning = false;
    }

    void monitor() {
        while (isRunning) {
            for (auto &slave : slaveNodes) {
                if (!checkHealth(slave)) {
                    std::cout << "Slave node unhealthy. Initiating failover..." << std::endl;
                    masterNode.manualFailover(slave->getVersion());
                }
            }
            std::this_thread::sleep_for(std::chrono::seconds(3)); // Health check interval
        }
    }

private:
    bool checkHealth(SlaveNode* slave) {
        // Simulated health check logic
        return slave->getVersion() > 0;
    }

    MasterNode &masterNode;
    std::vector<SlaveNode*> slaveNodes;
    bool isRunning;
};

int main() {
    MasterNode master;
    SlaveNode slave1(1);
    SlaveNode slave2(2);
    SlaveNode slave3(3);

    master.addSlave(&slave1);
    master.addSlave(&slave2);
    master.addSlave(&slave3);

    HealthChecker healthChecker(master, {&slave1, &slave2, &slave3});
    healthChecker.start();

    master.updateData("Initial data");
    std::this_thread::sleep_for(std::chrono::seconds(1));

    master.updateData("Updated data after modification");
    std::this_thread::sleep_for(std::chrono::seconds(1));

    // Simulate slave node failover
    std::cout << "Simulating failover for slave 2..." << std::endl;
    slave2.updateData("Stale data", 0); // Simulating slave failure

    master.manualFailover(2);
    std::this_thread::sleep_for(std::chrono::seconds(3));

    healthChecker.stop();

    return 0;
}