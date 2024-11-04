import unittest
import subprocess
import time
from coordination.membership.GossipProtocol import GossipProtocol

class CoordinationTests(unittest.TestCase):
    def setUp(self):
        # Setup Raft nodes using subprocess for Java implementation
        self.raft_nodes = []
        for i in range(5):
            node = subprocess.Popen(
                ['java', '-jar', 'RaftNode.jar', str(i), '5'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.raft_nodes.append(node)

        # Start the HeartbeatManager (C++ binary) using subprocess
        self.heartbeat_manager_process = subprocess.Popen(
            ['./HeartbeatManager'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Initialize the Gossip Protocol (Python class)
        self.gossip_protocol = GossipProtocol(self.raft_nodes)

    def test_leader_election(self):
        # Simulate leader election process by calling Java-based Raft nodes
        print("Starting leader election test")
        leader = None

        # Start elections on all nodes
        for node in self.raft_nodes:
            subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)
        
        # Wait for the election process to complete
        time.sleep(2)

        # Verify that only one node becomes the leader
        leader_count = 0
        for node in self.raft_nodes:
            node_output = node.stdout.readline().decode()
            if "LEADER" in node_output:
                leader_count += 1
                leader = node

        self.assertEqual(leader_count, 1)
        print(f"Leader elected: Node {leader.pid}")

    def test_leader_re_election_on_failure(self):
        print("Starting leader re-election test")
        leader = None

        # Start elections and identify leader
        for node in self.raft_nodes:
            subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)
        
        time.sleep(2)
        
        for node in self.raft_nodes:
            node_output = node.stdout.readline().decode()
            if "LEADER" in node_output:
                leader = node
                break
        
        print(f"Initial leader: Node {leader.pid}")

        # Simulate leader failure
        leader.terminate()
        leader.wait()

        # Trigger re-election
        time.sleep(1)
        for node in self.raft_nodes:
            if node != leader:
                subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)

        time.sleep(2)

        # Verify new leader
        new_leader_count = 0
        new_leader = None
        for node in self.raft_nodes:
            if node != leader:
                node_output = node.stdout.readline().decode()
                if "LEADER" in node_output:
                    new_leader_count += 1
                    new_leader = node

        self.assertEqual(new_leader_count, 1)
        print(f"New leader elected: Node {new_leader.pid}")

    def test_gossip_protocol_membership(self):
        print("Starting gossip protocol membership test")

        # Test gossip protocol for membership updates
        new_node = subprocess.Popen(['java', '-jar', 'RaftNode.jar', '5', '6'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.gossip_protocol.add_node(new_node)

        time.sleep(1)

        # Check if all nodes are aware of the new node
        for node in self.gossip_protocol.get_members():
            self.assertIn(new_node.pid, self.gossip_protocol.get_members())
        print(f"New node {new_node.pid} added to the cluster")

    def test_membership_removal(self):
        print("Starting membership removal test")

        # Remove a node from the membership via GossipProtocol
        remove_node = self.raft_nodes[0]
        self.gossip_protocol.remove_node(remove_node)

        time.sleep(1)

        # Check if all nodes have removed the node
        for node in self.gossip_protocol.get_members():
            self.assertNotIn(remove_node.pid, self.gossip_protocol.get_members())
        print(f"Node {remove_node.pid} removed from the cluster")

    def test_heartbeat_detection(self):
        print("Starting heartbeat failure detection test")

        failing_node = self.raft_nodes[2]

        # Simulate node failure in the C++ HeartbeatManager
        failing_node.terminate()
        failing_node.wait()

        time.sleep(2)

        # Check if HeartbeatManager detects the failure
        failed_output = self.heartbeat_manager_process.stdout.readline().decode()
        self.assertIn(f"Node {failing_node.pid} failed", failed_output)
        print(f"Node {failing_node.pid} detected as failed")

    def test_leader_heartbeat(self):
        print("Starting leader heartbeat test")

        # Start elections and identify leader
        leader = None
        for node in self.raft_nodes:
            subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)
        
        time.sleep(2)

        for node in self.raft_nodes:
            node_output = node.stdout.readline().decode()
            if "LEADER" in node_output:
                leader = node
                break

        # Verify that the leader is sending heartbeats (monitored by HeartbeatManager)
        time.sleep(2)
        heartbeat_output = self.heartbeat_manager_process.stdout.readline().decode()
        self.assertNotIn(f"Leader {leader.pid} failed", heartbeat_output)
        print(f"Leader {leader.pid} is sending heartbeats")

    def test_heartbeat_failover(self):
        print("Starting heartbeat failover test")

        leader = None
        for node in self.raft_nodes:
            subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)

        time.sleep(2)

        # Identify the leader
        for node in self.raft_nodes:
            node_output = node.stdout.readline().decode()
            if "LEADER" in node_output:
                leader = node
                break

        # Simulate leader failure
        leader.terminate()
        leader.wait()

        time.sleep(2)

        # Verify that HeartbeatManager triggers failover
        failover_output = self.heartbeat_manager_process.stdout.readline().decode()
        self.assertIn(f"Leader {leader.pid} failed", failover_output)
        print(f"Leader {leader.pid} failed and failover triggered")

        # Re-elect a new leader
        new_leader = None
        for node in self.raft_nodes:
            if node != leader:
                subprocess.run(['java', '-jar', 'RaftNode.jar', 'start-election'], check=True)

        time.sleep(2)
        for node in self.raft_nodes:
            node_output = node.stdout.readline().decode()
            if "LEADER" in node_output:
                new_leader = node
                break

        self.assertNotEqual(leader.pid, new_leader.pid)
        print(f"New leader after failover: Node {new_leader.pid}")

    def tearDown(self):
        # Clean up the processes
        for node in self.raft_nodes:
            node.terminate()
            node.wait()

        self.heartbeat_manager_process.terminate()
        self.heartbeat_manager_process.wait()

        self.gossip_protocol.stop()

if __name__ == "__main__":
    unittest.main()