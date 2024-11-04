#include <iostream>
#include <vector>
#include <map>
#include <algorithm>
#include <string>
#include <mutex>
#include <thread>
#include <condition_variable>
#include <chrono>

using namespace std;

class Node {
public:
    int id;
    string value;
    int highestProposalNum;
    int acceptedProposalNum;
    string acceptedValue;
    mutex mtx;
    condition_variable cv;
    bool isLeader;

    Node(int nodeId) {
        id = nodeId;
        highestProposalNum = -1;
        acceptedProposalNum = -1;
        isLeader = false;
    }

    bool propose(int proposalNum, string proposedValue) {
        lock_guard<mutex> lock(mtx);
        if (proposalNum > highestProposalNum) {
            highestProposalNum = proposalNum;
            return true;
        }
        return false;
    }

    bool accept(int proposalNum, string proposedValue) {
        lock_guard<mutex> lock(mtx);
        if (proposalNum >= highestProposalNum) {
            acceptedProposalNum = proposalNum;
            acceptedValue = proposedValue;
            cv.notify_all();
            return true;
        }
        return false;
    }

    void learn(string learnedValue) {
        lock_guard<mutex> lock(mtx);
        value = learnedValue;
        cout << "Node " << id << " learned value: " << value << endl;
    }
};

class Paxos {
private:
    vector<Node*> nodes;
    int quorumSize;

public:
    Paxos(vector<Node*> clusterNodes) {
        nodes = clusterNodes;
        quorumSize = nodes.size() / 2 + 1;
    }

    bool preparePhase(int proposerId, int proposalNum) {
        int promises = 0;
        for (auto node : nodes) {
            if (node->propose(proposalNum, "")) {
                promises++;
            }
        }
        return promises >= quorumSize;
    }

    bool acceptPhase(int proposerId, int proposalNum, string proposedValue) {
        int accepts = 0;
        for (auto node : nodes) {
            if (node->accept(proposalNum, proposedValue)) {
                accepts++;
            }
        }
        return accepts >= quorumSize;
    }

    void learnPhase(int proposerId, string value) {
        for (auto node : nodes) {
            node->learn(value);
        }
    }

    void runPaxos(int proposerId, int proposalNum, string value) {
        if (preparePhase(proposerId, proposalNum)) {
            if (acceptPhase(proposerId, proposalNum, value)) {
                learnPhase(proposerId, value);
            }
        }
    }
};

class ConsensusCluster {
private:
    vector<Node*> nodes;
    Paxos* paxos;

public:
    ConsensusCluster(int nodeCount) {
        for (int i = 0; i < nodeCount; i++) {
            nodes.push_back(new Node(i));
        }
        paxos = new Paxos(nodes);
    }

    void proposeValue(int proposerId, string value) {
        static int proposalNum = 0;
        paxos->runPaxos(proposerId, ++proposalNum, value);
    }

    ~ConsensusCluster() {
        for (auto node : nodes) {
            delete node;
        }
        delete paxos;
    }
};

void startProposer(ConsensusCluster* cluster, int proposerId, string value) {
    this_thread::sleep_for(chrono::milliseconds(100)); 
    cluster->proposeValue(proposerId, value);
}

int main() {
    // Initialize a cluster of 5 nodes
    ConsensusCluster* cluster = new ConsensusCluster(5);

    // Run proposals from multiple proposers
    thread proposer1(startProposer, cluster, 0, "ValueA");
    thread proposer2(startProposer, cluster, 1, "ValueB");

    proposer1.join();
    proposer2.join();

    delete cluster;
    return 0;
}