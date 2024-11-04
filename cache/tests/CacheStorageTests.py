import unittest
import subprocess
import os
from persistent_cache.DiskStore import DiskStore

class CacheStorageTests(unittest.TestCase):

    def setUp(self):
        # Setup for each test case
        self.disk_store = DiskStore(directory='./test_cache', max_size=100)

    def tearDown(self):
        # Cleanup after each test case
        if os.path.exists('./test_cache'):
            for file in os.listdir('./test_cache'):
                file_path = os.path.join('./test_cache', file)
                os.unlink(file_path)
            os.rmdir('./test_cache')

    # Utility to call external processes for eviction policies and C++ cache stores

    def run_cpp_binary(self, binary_path, *args):
        # Function to call a C++ binary with arguments
        result = subprocess.run([binary_path] + list(args), capture_output=True, text=True)
        return result.stdout.strip()

    def run_java_class(self, class_name, *args):
        # Function to call a Java class with arguments
        result = subprocess.run(['java', class_name] + list(args), capture_output=True, text=True)
        return result.stdout.strip()

    # In-memory cache tests (using subprocess to call C++ binary)
    def test_in_memory_store_add(self):
        # Add elements using C++ InMemoryStore binary
        output = self.run_cpp_binary('./bin/InMemoryStore', 'add', 'key1', 'value1')
        self.assertIn('Added', output)
        output = self.run_cpp_binary('./bin/InMemoryStore', 'add', 'key2', 'value2')
        self.assertIn('Added', output)

    def test_in_memory_store_evict(self):
        # Test eviction when max size is reached
        for i in range(10):
            self.run_cpp_binary('./bin/InMemoryStore', 'add', f'key{i}', f'value{i}')
        output = self.run_cpp_binary('./bin/InMemoryStore', 'add', 'key10', 'value10') 
        self.assertIn('Evicted', output)
        output = self.run_cpp_binary('./bin/InMemoryStore', 'get', 'key0')
        self.assertEqual(output, 'NULL') 

    # LRU policy tests (using subprocess to call Java class)
    def test_lru_policy_add(self):
        # Test LRU policy with multiple inserts using Java class
        for i in range(5):
            output = self.run_java_class('eviction_policies.LRUPolicy', 'record_access', f'key{i}')
        output = self.run_java_class('eviction_policies.LRUPolicy', 'get_least_recently_used')
        self.assertEqual(output, 'key0')

    def test_lru_policy_eviction(self):
        # Test eviction using LRU policy
        for i in range(5):
            output = self.run_java_class('eviction_policies.LRUPolicy', 'record_access', f'key{i}')
        self.run_java_class('eviction_policies.LRUPolicy', 'record_access', 'key0')  
        output = self.run_java_class('eviction_policies.LRUPolicy', 'get_least_recently_used')
        self.assertEqual(output, 'key1')

    # LFU policy tests (using subprocess to call Java class)
    def test_lfu_policy_add(self):
        # Test LFU policy with inserts using Java class
        for i in range(3):
            self.run_java_class('eviction_policies.LFUPolicy', 'record_access', 'key1')
        for i in range(2):
            self.run_java_class('eviction_policies.LFUPolicy', 'record_access', 'key2')
        output = self.run_java_class('eviction_policies.LFUPolicy', 'get_least_frequently_used')
        self.assertEqual(output, 'key2')

    def test_lfu_policy_eviction(self):
        # Test eviction using LFU policy
        for i in range(5):
            self.run_java_class('eviction_policies.LFUPolicy', 'record_access', f'key{i}')
        self.run_java_class('eviction_policies.LFUPolicy', 'record_access', 'key0')
        output = self.run_java_class('eviction_policies.LFUPolicy', 'get_least_frequently_used')
        self.assertEqual(output, 'key1')

    # FIFO policy tests (using subprocess to call C++ binary)
    def test_fifo_policy_add(self):
        # Test FIFO policy with inserts using C++ binary
        for i in range(5):
            output = self.run_cpp_binary('./bin/FIFOPolicy', 'record_insert', f'key{i}')
        output = self.run_cpp_binary('./bin/FIFOPolicy', 'get_first_inserted')
        self.assertEqual(output, 'key0')

    def test_fifo_policy_eviction(self):
        # Test eviction using FIFO policy
        for i in range(5):
            output = self.run_cpp_binary('./bin/FIFOPolicy', 'record_insert', f'key{i}')
        output = self.run_cpp_binary('./bin/FIFOPolicy', 'get_first_inserted')
        self.assertEqual(output, 'key0')
        self.run_cpp_binary('./bin/FIFOPolicy', 'evict_first_inserted')
        output = self.run_cpp_binary('./bin/FIFOPolicy', 'get_first_inserted')
        self.assertEqual(output, 'key1')

    # Disk store tests (as per original)

    def test_disk_store_add(self):
        # Test adding elements to disk store
        self.disk_store.add('key1', 'value1')
        self.disk_store.add('key2', 'value2')
        self.assertTrue(os.path.exists('./test_cache/key1'))
        self.assertTrue(os.path.exists('./test_cache/key2'))

    def test_disk_store_get(self):
        # Test retrieving elements from disk store
        self.disk_store.add('key1', 'value1')
        self.disk_store.add('key2', 'value2')
        self.assertEqual(self.disk_store.get('key1'), 'value1')
        self.assertEqual(self.disk_store.get('key2'), 'value2')

    def test_disk_store_evict(self):
        # Test eviction when disk store max size is reached
        for i in range(10):
            self.disk_store.add(f'key{i}', f'value{i}')
        self.disk_store.add('key10', 'value10')  
        self.assertIsNone(self.disk_store.get('key0')) 

    def test_disk_store_remove(self):
        # Test removing elements from disk store
        self.disk_store.add('key1', 'value1')
        self.disk_store.remove('key1')
        self.assertFalse(os.path.exists('./test_cache/key1'))

if __name__ == '__main__':
    unittest.main()