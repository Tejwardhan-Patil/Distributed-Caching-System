import threading
import time
import random
from collections import defaultdict

class ConflictResolver:
    def resolve(self, key, versions):
        # Simple Last-Write-Wins (LWW) conflict resolution strategy
        return max(versions, key=lambda x: x['timestamp'])

class Node:
    def __init__(self, node_id, replication_group, conflict_resolver):
        self.node_id = node_id
        self.store = {}
        self.lock = threading.Lock()
        self.replication_group = replication_group
        self.conflict_resolver = conflict_resolver
        self.log = defaultdict(list)  # Keeps versions of each key for conflict resolution

    def get(self, key):
        with self.lock:
            return self.store.get(key, None)

    def put(self, key, value):
        with self.lock:
            timestamp = time.time()
            version = {'value': value, 'timestamp': timestamp, 'node_id': self.node_id}
            self.store[key] = version['value']
            self.log[key].append(version)
            self.replicate(key, version)

    def replicate(self, key, version):
        for node in self.replication_group:
            if node.node_id != self.node_id:
                node.receive_replica(key, version)

    def receive_replica(self, key, version):
        with self.lock:
            self.log[key].append(version)
            resolved_value = self.conflict_resolver.resolve(key, self.log[key])
            self.store[key] = resolved_value['value']

class MultiMasterReplication:
    def __init__(self, nodes, conflict_resolver=None):
        self.nodes = nodes
        self.conflict_resolver = conflict_resolver or ConflictResolver()

    def add_node(self, node):
        self.nodes.append(node)

    def remove_node(self, node):
        self.nodes.remove(node)

    def put(self, key, value, node_id):
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if node:
            node.put(key, value)
        else:
            raise ValueError("Node not found")

    def get(self, key, node_id):
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if node:
            return node.get(key)
        else:
            raise ValueError("Node not found")

    def simulate_conflict(self, key, conflicting_values):
        # Simulates a conflict by applying conflicting writes
        for i, value in enumerate(conflicting_values):
            self.put(key, value, self.nodes[i].node_id)

    def print_store(self):
        for node in self.nodes:
            print(f"Node {node.node_id} store: {node.store}")

def simulate_multi_master():
    # Create nodes
    conflict_resolver = ConflictResolver()
    nodes = [Node(node_id=i, replication_group=[], conflict_resolver=conflict_resolver) for i in range(3)]

    # Assign replication group
    for node in nodes:
        node.replication_group = nodes

    # Create Multi-Master replication group
    replication = MultiMasterReplication(nodes)

    # Perform some writes
    replication.put('key1', 'value1', node_id=0)
    replication.put('key1', 'value2', node_id=1)
    replication.put('key2', 'value3', node_id=2)

    # Simulate conflicting writes
    replication.simulate_conflict('key3', ['value_conflict_1', 'value_conflict_2', 'value_conflict_3'])

    # Print the stores
    replication.print_store()

if __name__ == "__main__":
    simulate_multi_master()