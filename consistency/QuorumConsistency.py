import threading
import random
from enum import Enum
from collections import defaultdict

class QuorumType(Enum):
    READ = 'READ'
    WRITE = 'WRITE'

class Replica:
    def __init__(self, id):
        self.id = id
        self.data_store = {}

    def write(self, key, value):
        self.data_store[key] = value
        return True

    def read(self, key):
        return self.data_store.get(key, None)

class QuorumConsistency:
    def __init__(self, replicas, quorum_size):
        self.replicas = replicas  # List of replica nodes
        self.quorum_size = quorum_size
        self.lock = threading.Lock()

    def quorum_operation(self, operation_type, key, value=None):
        selected_replicas = random.sample(self.replicas, self.quorum_size)

        if operation_type == QuorumType.READ:
            return self._read_quorum(key, selected_replicas)
        elif operation_type == QuorumType.WRITE:
            return self._write_quorum(key, value, selected_replicas)
        else:
            raise ValueError("Invalid quorum operation type.")

    def _write_quorum(self, key, value, selected_replicas):
        ack_count = 0
        for replica in selected_replicas:
            if replica.write(key, value):
                ack_count += 1
        return ack_count >= self.quorum_size

    def _read_quorum(self, key, selected_replicas):
        versioned_values = defaultdict(list)
        for replica in selected_replicas:
            value = replica.read(key)
            if value is not None:
                versioned_values[value].append(replica.id)
        
        if not versioned_values:
            return None
        
        return max(versioned_values.items(), key=lambda x: len(x[1]))[0]  # Return the most common value

class DistributedCache:
    def __init__(self, num_replicas, quorum_size):
        self.replicas = [Replica(i) for i in range(num_replicas)]
        self.quorum = QuorumConsistency(self.replicas, quorum_size)
    
    def write(self, key, value):
        return self.quorum.quorum_operation(QuorumType.WRITE, key, value)

    def read(self, key):
        return self.quorum.quorum_operation(QuorumType.READ, key)

    def read_all(self, key):
        # This function fetches data from all replicas for monitoring
        return {replica.id: replica.read(key) for replica in self.replicas}

# Testing quorum consistency
if __name__ == "__main__":
    # Parameters
    num_replicas = 5
    quorum_size = 3
    cache = DistributedCache(num_replicas, quorum_size)

    # Write operation
    print("Writing 'key1' with value 'value1' using quorum:")
    result = cache.write('key1', 'value1')
    print("Write successful:", result)

    # Read operation
    print("\nReading 'key1' with quorum:")
    result = cache.read('key1')
    print("Value read:", result)

    # Read from all replicas for debugging
    print("\nReading 'key1' from all replicas:")
    replica_data = cache.read_all('key1')
    for replica_id, data in replica_data.items():
        print(f"Replica {replica_id}: {data}")

    # Write another value
    print("\nWriting 'key1' with new value 'value2':")
    result = cache.write('key1', 'value2')
    print("Write successful:", result)

    # Read again
    print("\nReading 'key1' after new write:")
    result = cache.read('key1')
    print("Value read:", result)

    print("\nReading from all replicas after second write:")
    replica_data = cache.read_all('key1')
    for replica_id, data in replica_data.items():
        print(f"Replica {replica_id}: {data}")