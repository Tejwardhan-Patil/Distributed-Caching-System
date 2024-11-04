#include <iostream>
#include <thread>
#include <chrono>
#include <atomic>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <unordered_map>
#include <functional>

using namespace std;

class HeartbeatManager {
private:
    atomic<bool> running;
    atomic<int> heartbeatIntervalMs;
    atomic<int> failureThresholdMs;

    struct Node {
        string id;
        atomic<bool> alive;
        atomic<int> lastHeartbeatTimestamp;
    };

    unordered_map<string, Node> nodes;
    mutex nodesMutex;
    condition_variable cv;
    thread monitorThread;

    function<void(const string&)> onNodeFailureCallback;

public:
    HeartbeatManager(int heartbeatInterval, int failureThreshold)
        : heartbeatIntervalMs(heartbeatInterval), failureThresholdMs(failureThreshold), running(true) {}

    void start() {
        monitorThread = thread(&HeartbeatManager::monitorNodes, this);
    }

    void stop() {
        running = false;
        cv.notify_all();
        if (monitorThread.joinable()) {
            monitorThread.join();
        }
    }

    void registerNode(const string& nodeId) {
        lock_guard<mutex> lock(nodesMutex);
        nodes[nodeId] = Node{ nodeId, true, static_cast<int>(chrono::system_clock::now().time_since_epoch().count()) };
    }

    void removeNode(const string& nodeId) {
        lock_guard<mutex> lock(nodesMutex);
        nodes.erase(nodeId);
    }

    void receiveHeartbeat(const string& nodeId) {
        lock_guard<mutex> lock(nodesMutex);
        if (nodes.find(nodeId) != nodes.end()) {
            nodes[nodeId].lastHeartbeatTimestamp = static_cast<int>(chrono::system_clock::now().time_since_epoch().count());
            nodes[nodeId].alive = true;
        }
    }

    void setNodeFailureCallback(function<void(const string&)> callback) {
        onNodeFailureCallback = callback;
    }

    void setHeartbeatInterval(int intervalMs) {
        heartbeatIntervalMs = intervalMs;
    }

    void setFailureThreshold(int thresholdMs) {
        failureThresholdMs = thresholdMs;
    }

private:
    void monitorNodes() {
        while (running) {
            {
                lock_guard<mutex> lock(nodesMutex);
                auto currentTime = static_cast<int>(chrono::system_clock::now().time_since_epoch().count());

                for (auto& pair : nodes) {
                    Node& node = pair.second;
                    if (node.alive && currentTime - node.lastHeartbeatTimestamp > failureThresholdMs) {
                        node.alive = false;
                        if (onNodeFailureCallback) {
                            onNodeFailureCallback(node.id);
                        }
                    }
                }
            }

            this_thread::sleep_for(chrono::milliseconds(heartbeatIntervalMs));
            cv.notify_all();
        }
    }
};

int main() {
    HeartbeatManager manager(1000, 3000); // Heartbeat interval: 1 second, failure threshold: 3 seconds

    manager.setNodeFailureCallback([](const string& nodeId) {
        cout << "Node " << nodeId << " failed!" << endl;
    });

    manager.start();

    // Simulating node heartbeats
    manager.registerNode("Node1");
    manager.registerNode("Node2");

    this_thread::sleep_for(chrono::milliseconds(1500));
    manager.receiveHeartbeat("Node1");

    this_thread::sleep_for(chrono::milliseconds(1500));
    manager.receiveHeartbeat("Node2");

    this_thread::sleep_for(chrono::milliseconds(5000));

    manager.stop();

    return 0;
}