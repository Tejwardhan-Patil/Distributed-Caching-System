import unittest
import subprocess
import json
from consistency.QuorumConsistency import QuorumConsistency
from distributed.replication.MultiMasterReplication import MultiMasterReplication

class ConsistencyManagementTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up resources before any tests are run."""
        # Setup for Python components
        cls.quorum_consistency = QuorumConsistency()
        cls.multi_master_replication = MultiMasterReplication()
        
        # Path to the Java class for EventualConsistency
        cls.eventual_consistency_class = "consistency.EventualConsistency"

    def setUp(self):
        """Set up before each individual test."""
        self.quorum_consistency.reset()
        self.multi_master_replication.reset()

    def run_java_eventual_consistency(self, method, *args):
        """Helper method to call Java EventualConsistency class methods via subprocess."""
        command = ["java", self.eventual_consistency_class, method] + list(map(str, args))
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()

    def test_eventual_consistency_basic(self):
        """Test if data eventually becomes consistent across nodes."""
        self.run_java_eventual_consistency("write", "key1", "value1")
        result = self.run_java_eventual_consistency("read", "key1")
        self.assertEqual(result, "value1")

    def test_eventual_consistency_eventual_sync(self):
        """Test if eventual consistency synchronizes data across multiple nodes."""
        self.run_java_eventual_consistency("write", "key2", "value2", "1")
        result = self.run_java_eventual_consistency("read", "key2", "2")
        self.assertNotEqual(result, "value2")
        
        # Simulate synchronization in Java
        self.run_java_eventual_consistency("synchronize", "2")
        result_after_sync = self.run_java_eventual_consistency("read", "key2", "2")
        self.assertEqual(result_after_sync, "value2")

    def test_eventual_consistency_network_partition(self):
        """Test eventual consistency with a simulated network partition."""
        self.run_java_eventual_consistency("write", "key3", "value3", "1")
        
        # Simulate network partition in Java
        self.run_java_eventual_consistency("simulateNetworkPartition", "2")
        self.run_java_eventual_consistency("write", "key3", "new_value3", "2")
        
        result_node1 = self.run_java_eventual_consistency("read", "key3", "1")
        self.assertNotEqual(result_node1, "new_value3")

        # Recover and synchronize
        self.run_java_eventual_consistency("recoverNetworkPartition", "2")
        self.run_java_eventual_consistency("synchronizeAll")
        final_result = self.run_java_eventual_consistency("read", "key3", "1")
        self.assertEqual(final_result, "new_value3")

    def test_quorum_consistency_basic_read(self):
        """Test quorum-based consistency model with successful read operations."""
        self.quorum_consistency.write('key4', 'value4')
        result = self.quorum_consistency.read('key4')
        self.assertEqual(result, 'value4')

    def test_quorum_consistency_failure(self):
        """Test quorum-based read failure when quorum is not reached."""
        self.quorum_consistency.write('key5', 'value5')
        
        # Simulate node failures
        self.quorum_consistency.fail_node(1)
        self.quorum_consistency.fail_node(2)
        
        result = self.quorum_consistency.read('key5')
        self.assertIsNone(result, "Read should fail when quorum is not reached.")

    def test_quorum_consistency_write(self):
        """Test quorum-based write consistency."""
        self.quorum_consistency.write('key6', 'value6')
        self.assertEqual(self.quorum_consistency.read('key6'), 'value6')

        # Simulate failure of a node after write
        self.quorum_consistency.fail_node(2)
        self.assertEqual(self.quorum_consistency.read('key6'), 'value6')

    def test_multi_master_conflict_resolution(self):
        """Test conflict resolution in multi-master replication."""
        self.multi_master_replication.write('key7', 'value7', node_id=1)
        self.multi_master_replication.write('key7', 'value8', node_id=2)
        
        # Conflict resolution
        resolved_value = self.multi_master_replication.resolve_conflict('key7')
        self.assertIn(resolved_value, ['value7', 'value8'])

    def test_multi_master_last_write_wins(self):
        """Test last-write-wins conflict resolution in multi-master replication."""
        self.multi_master_replication.write('key8', 'value8', node_id=1)
        self.multi_master_replication.write('key8', 'new_value8', node_id=2)
        
        resolved_value = self.multi_master_replication.resolve_conflict('key8', strategy='last_write_wins')
        self.assertEqual(resolved_value, 'new_value8')

    def test_multi_master_vector_clock_resolution(self):
        """Test conflict resolution using vector clocks in multi-master replication."""
        self.multi_master_replication.write('key9', 'value9', node_id=1)
        self.multi_master_replication.write('key9', 'new_value9', node_id=2)
        
        resolved_value = self.multi_master_replication.resolve_conflict('key9', strategy='vector_clocks')
        self.assertEqual(resolved_value, 'new_value9')

    def tearDown(self):
        """Clean up after each test."""
        self.quorum_consistency.reset()
        self.multi_master_replication.reset()

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests are run."""
        del cls.quorum_consistency
        del cls.multi_master_replication

if __name__ == '__main__':
    unittest.main()