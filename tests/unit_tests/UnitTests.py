import unittest
import subprocess
import json
from cache.persistent_cache.DiskStore import DiskStore
from cache.serialization.JsonSerializer import JsonSerializer
from distributed.replication.MultiMasterReplication import MultiMasterReplication
from consistency.QuorumConsistency import QuorumConsistency


class TestInMemoryStore(unittest.TestCase):

    def run_cpp_in_memory_store(self, command):
        """ Helper method to invoke the InMemoryStore C++ binary using subprocess. """
        result = subprocess.run(['/cache/InMemoryStore', '--command'] + command,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout

    def test_in_memory_store_set_get(self):
        # Set a value and retrieve it
        self.run_cpp_in_memory_store(["set", "key1", "value1"])
        result = self.run_cpp_in_memory_store(["get", "key1"])
        self.assertEqual(result.strip(), "value1")

    def test_in_memory_store_eviction_lru(self):
        self.run_cpp_in_memory_store(["set_eviction_policy", "LRU"])
        self.run_cpp_in_memory_store(["set", "key1", "value1"])
        self.run_cpp_in_memory_store(["set", "key2", "value2"])
        self.run_cpp_in_memory_store(["set", "key3", "value3"])
        self.run_cpp_in_memory_store(["set", "key4", "value4"])  
        result = self.run_cpp_in_memory_store(["get", "key1"])  
        self.assertEqual(result.strip(), "None")
        result = self.run_cpp_in_memory_store(["get", "key4"])
        self.assertEqual(result.strip(), "value4")


class TestDiskStore(unittest.TestCase):

    def setUp(self):
        self.disk_store = DiskStore("/tmp/disk_store")

    def test_disk_store_write_read(self):
        self.disk_store.write("key1", "value1")
        result = self.disk_store.read("key1")
        self.assertEqual(result, "value1")


class TestJsonSerializer(unittest.TestCase):

    def setUp(self):
        self.serializer = JsonSerializer()

    def test_json_serializer_serialize(self):
        data = {"key": "value"}
        serialized_data = self.serializer.serialize(data)
        self.assertEqual(serialized_data, '{"key": "value"}')

    def test_json_serializer_deserialize(self):
        serialized_data = '{"key": "value"}'
        deserialized_data = self.serializer.deserialize(serialized_data)
        self.assertEqual(deserialized_data, {"key": "value"})


class TestMultiMasterReplication(unittest.TestCase):

    def setUp(self):
        self.replication = MultiMasterReplication()

    def test_multi_master_replication_conflict_resolution(self):
        node1_data = {"key1": "value1"}
        node2_data = {"key1": "value2"}
        resolved_data = self.replication.resolve_conflict(node1_data, node2_data)
        self.assertEqual(resolved_data["key1"], "value2")  

    def test_multi_master_replication_sync(self):
        self.replication.update_node("key1", "value1")
        result = self.replication.sync_data()
        self.assertIn("key1", result)
        self.assertEqual(result["key1"], "value1")


class TestQuorumConsistency(unittest.TestCase):

    def setUp(self):
        self.quorum = QuorumConsistency()

    def test_quorum_consistency_read(self):
        self.quorum.write("key1", "value1", quorum=2)
        result = self.quorum.read("key1", quorum=2)
        self.assertEqual(result, "value1")

    def test_quorum_consistency_write(self):
        success = self.quorum.write("key1", "value1", quorum=2)
        self.assertTrue(success)


class TestLRUPolicy(unittest.TestCase):

    def run_java_lru_policy(self, command):
        """ Helper method to invoke the LRUPolicy Java class using subprocess. """
        result = subprocess.run(['java', '-cp', '/cache/eviction_policies', 'LRUPolicy'] + command,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout

    def test_lru_policy_eviction(self):
        self.run_java_lru_policy(["add", "key1"])
        self.run_java_lru_policy(["add", "key2"])
        self.run_java_lru_policy(["access", "key1"]) 
        self.run_java_lru_policy(["add", "key3"])  
        output = self.run_java_lru_policy(["get_all"])
        self.assertNotIn("key2", output)
        self.assertIn("key1", output)


class TestLFUPolicy(unittest.TestCase):

    def run_java_lfu_policy(self, command):
        """ Helper method to invoke the LFUPolicy Java class using subprocess. """
        result = subprocess.run(['java', '-cp', '/cache/eviction_policies', 'LFUPolicy'] + command,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout

    def test_lfu_policy_eviction(self):
        self.run_java_lfu_policy(["add", "key1"])
        self.run_java_lfu_policy(["add", "key2"])
        self.run_java_lfu_policy(["access", "key1"])  
        self.run_java_lfu_policy(["add", "key3"])  
        output = self.run_java_lfu_policy(["get_all"])
        self.assertNotIn("key2", output)
        self.assertIn("key1", output)


class TestFIFOPolicy(unittest.TestCase):

    def run_cpp_fifo_policy(self, command):
        """ Helper method to invoke the FIFOPolicy C++ binary using subprocess. """
        result = subprocess.run(['/cache/eviction_policies/FIFOPolicy', '--command'] + command,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout

    def test_fifo_policy_eviction(self):
        self.run_cpp_fifo_policy(["add", "key1"])
        self.run_cpp_fifo_policy(["add", "key2"])
        self.run_cpp_fifo_policy(["add", "key3"])
        self.run_cpp_fifo_policy(["add", "key4"])  
        output = self.run_cpp_fifo_policy(["get_all"])
        self.assertNotIn("key1", output)
        self.assertIn("key4", output)


if __name__ == '__main__':
    unittest.main()