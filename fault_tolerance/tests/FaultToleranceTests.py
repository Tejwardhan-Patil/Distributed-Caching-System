import unittest
import subprocess
import json
from fault_tolerance.data_recovery.SnapshotRecovery import SnapshotRecovery
from distributed.replication.MultiMasterReplication import MultiMasterReplication

class FaultToleranceTests(unittest.TestCase):

    def setUp(self):
        # Initialize SnapshotRecovery and MultiMasterReplication
        self.snapshot_recovery = SnapshotRecovery()
        self.replication = MultiMasterReplication()

    def run_failover_manager(self, command):
        """
        Run FailoverManager using subprocess (Java component).
        """
        java_command = ['java', '-cp', 'fault_tolerance/failover/', 'FailoverManager', command]
        result = subprocess.run(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f"FailoverManager failed: {result.stderr}")
        return result.stdout.strip()

    def run_log_based_recovery(self, command):
        """
        Run LogBasedRecovery using subprocess (C++ component).
        """
        cpp_command = ['./fault_tolerance/data_recovery/LogBasedRecovery', command]
        result = subprocess.run(cpp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f"LogBasedRecovery failed: {result.stderr}")
        return result.stdout.strip()

    def test_failover_trigger(self):
        """
        Test FailoverManager detects failure and triggers failover process.
        """
        # Add nodes and simulate failure via subprocess call to Java
        self.run_failover_manager('add_node node-1')
        self.run_failover_manager('add_node node-2')
        self.run_failover_manager('simulate_failure node-1')

        # Check failover triggered by invoking Java process
        failover_status = self.run_failover_manager('is_failover_triggered')
        self.assertEqual(failover_status, 'true')

    def test_failover_node_assignment(self):
        """
        Test that after failover, a new node is assigned to handle requests.
        """
        # Add nodes and simulate failure via subprocess call to Java
        self.run_failover_manager('add_node node-1')
        self.run_failover_manager('add_node node-2')
        self.run_failover_manager('simulate_failure node-1')

        # Check active node after failover
        active_node = self.run_failover_manager('get_active_node')
        self.assertEqual(active_node, 'node-2')

    def test_snapshot_recovery(self):
        """
        Test recovery process using snapshot data.
        """
        # Simulate snapshot recovery process
        self.snapshot_recovery.take_snapshot()
        data_before_failure = {'key1': 'value1', 'key2': 'value2'}
        self.snapshot_recovery.store_data(data_before_failure)

        # Simulate failure and recovery
        self.snapshot_recovery.simulate_failure()
        recovered_data = self.snapshot_recovery.recover_data()

        # Verify recovered data matches the original data
        self.assertEqual(recovered_data, data_before_failure)

    def test_log_based_recovery(self):
        """
        Test log-based recovery process after a failure using subprocess (C++).
        """
        # Write log entries via subprocess call to C++
        logs = [{'action': 'set', 'key': 'key1', 'value': 'value1'},
                {'action': 'set', 'key': 'key2', 'value': 'value2'}]
        
        for log in logs:
            log_command = json.dumps(log)
            self.run_log_based_recovery(f'write_log {log_command}')

        # Simulate failure and recovery via subprocess
        self.run_log_based_recovery('simulate_failure')
        recovered_data = self.run_log_based_recovery('recover_data')

        # Verify recovered data matches the log entries
        expected_data = {'key1': 'value1', 'key2': 'value2'}
        recovered_data_dict = json.loads(recovered_data)
        self.assertEqual(recovered_data_dict, expected_data)

    def test_replication_failover(self):
        """
        Test failover in a multi-master replication setup.
        """
        # Simulate multiple masters
        master1 = 'master-1'
        master2 = 'master-2'
        self.replication.add_master(master1)
        self.replication.add_master(master2)

        # Simulate master failure
        self.replication.simulate_failure(master1)

        # Ensure failover to the second master
        self.assertTrue(self.replication.is_failover_triggered())
        self.assertEqual(self.replication.get_active_master(), master2)

    def test_log_recovery_with_conflict(self):
        """
        Test log-based recovery with conflicting data using subprocess (C++).
        """
        # Write conflicting log entries via subprocess call to C++
        logs = [{'action': 'set', 'key': 'key1', 'value': 'old_value'},
                {'action': 'set', 'key': 'key1', 'value': 'new_value'}]
        
        for log in logs:
            log_command = json.dumps(log)
            self.run_log_based_recovery(f'write_log {log_command}')

        # Simulate failure and recovery via subprocess
        self.run_log_based_recovery('simulate_failure')
        recovered_data = self.run_log_based_recovery('recover_data')

        # Verify conflict resolution: key1 should have 'new_value'
        expected_data = {'key1': 'new_value'}
        recovered_data_dict = json.loads(recovered_data)
        self.assertEqual(recovered_data_dict, expected_data)

    def test_failover_without_available_nodes(self):
        """
        Test failover scenario when no nodes are available.
        """
        failed_node = 'node-1'
        self.run_failover_manager('add_node node-1')

        # Simulate node failure with no backup nodes via subprocess
        self.run_failover_manager(f'simulate_failure {failed_node}')

        # Check that failover manager correctly identifies no available nodes
        available_nodes = self.run_failover_manager('has_available_nodes')
        self.assertEqual(available_nodes, 'false')

    def tearDown(self):
        # Clean up any state
        self.run_failover_manager('reset')
        self.run_log_based_recovery('reset')
        self.snapshot_recovery.reset()
        self.replication.reset()

if __name__ == '__main__':
    unittest.main()