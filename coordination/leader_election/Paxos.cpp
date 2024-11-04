#include <iostream>
#include <vector>
#include <unordered_map>
#include <set>
#include <optional>
#include <string>
#include <mutex>
#include <thread>

class PaxosNode {
public:
    PaxosNode(int id) : node_id(id), promised_id(-1), accepted_id(-1) {}

    // Proposer phase 1: Prepare
    bool prepare(int proposal_id) {
        std::lock_guard<std::mutex> lock(mtx);
        if (proposal_id > promised_id) {
            promised_id = proposal_id;
            return true;
        }
        return false;
    }

    // Proposer phase 2: Accept
    bool accept(int proposal_id, const std::string &value) {
        std::lock_guard<std::mutex> lock(mtx);
        if (proposal_id >= promised_id) {
            promised_id = proposal_id;
            accepted_id = proposal_id;
            accepted_value = value;
            return true;
        }
        return false;
    }

    // Learner phase: Learn
    std::optional<std::string> learn() {
        std::lock_guard<std::mutex> lock(mtx);
        return accepted_value;
    }

    // Getter for node ID
    int get_node_id() const {
        return node_id;
    }

private:
    int node_id;
    int promised_id;
    int accepted_id;
    std::optional<std::string> accepted_value;
    std::mutex mtx;
};

class PaxosSystem {
public:
    PaxosSystem(int num_nodes) {
        for (int i = 0; i < num_nodes; ++i) {
            nodes.push_back(new PaxosNode(i));
        }
    }

    ~PaxosSystem() {
        for (PaxosNode *node : nodes) {
            delete node;
        }
    }

    // Proposer initiates a new proposal
    bool propose(int proposer_id, int proposal_id, const std::string &value) {
        int num_prepare_accepted = 0;
        std::unordered_map<int, std::string> accepted_values;
        std::optional<std::string> decided_value;

        // Phase 1: Prepare
        for (PaxosNode *node : nodes) {
            if (node->prepare(proposal_id)) {
                ++num_prepare_accepted;
                auto learned_value = node->learn();
                if (learned_value) {
                    accepted_values[node->get_node_id()] = *learned_value;
                }
            }
        }

        // Majority must accept prepare
        if (num_prepare_accepted <= nodes.size() / 2) {
            return false;
        }

        // Phase 2: Accept
        int num_accept_accepted = 0;
        if (!accepted_values.empty()) {
            decided_value = accepted_values.begin()->second;
        } else {
            decided_value = value;
        }

        for (PaxosNode *node : nodes) {
            if (node->accept(proposal_id, *decided_value)) {
                ++num_accept_accepted;
            }
        }

        // Majority must accept the proposal
        return num_accept_accepted > nodes.size() / 2;
    }

private:
    std::vector<PaxosNode *> nodes;
};

void proposer(PaxosSystem &system, int proposer_id, const std::string &value) {
    int proposal_id = proposer_id * 1000 + rand() % 1000;
    if (system.propose(proposer_id, proposal_id, value)) {
        std::cout << "Proposer " << proposer_id << " proposal " << proposal_id << " accepted.\n";
    } else {
        std::cout << "Proposer " << proposer_id << " proposal " << proposal_id << " rejected.\n";
    }
}

int main() {
    const int num_nodes = 5;
    PaxosSystem system(num_nodes);

    std::thread t1(proposer, std::ref(system), 1, "Value_A");
    std::thread t2(proposer, std::ref(system), 2, "Value_B");

    t1.join();
    t2.join();

    return 0;
}