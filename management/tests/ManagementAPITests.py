import unittest
import requests
from cache_api.API import app

class ManagementAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.base_url = "http://localhost:5000/api"

    def test_api_health_check(self):
        """Test if the API health check endpoint is working"""
        response = self.client.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'OK')

    def test_add_cache_entry(self):
        """Test adding a cache entry via API"""
        cache_key = 'test_key'
        cache_value = 'test_value'
        response = self.client.post(f"{self.base_url}/cache", json={
            'key': cache_key,
            'value': cache_value
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'Entry added successfully')

    def test_get_cache_entry(self):
        """Test retrieving a cache entry via API"""
        cache_key = 'test_key'
        response = self.client.get(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['key'], cache_key)
        self.assertEqual(response.json['value'], 'test_value')

    def test_update_cache_entry(self):
        """Test updating a cache entry via API"""
        cache_key = 'test_key'
        new_value = 'updated_value'
        response = self.client.put(f"{self.base_url}/cache/{cache_key}", json={
            'value': new_value
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Entry updated successfully')
        # Verify update
        response = self.client.get(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.json['value'], new_value)

    def test_delete_cache_entry(self):
        """Test deleting a cache entry via API"""
        cache_key = 'test_key'
        response = self.client.delete(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Entry deleted successfully')
        # Verify deletion
        response = self.client.get(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.status_code, 404)

    def test_add_invalid_cache_entry(self):
        """Test adding a cache entry with invalid data"""
        response = self.client.post(f"{self.base_url}/cache", json={
            'key': '',
            'value': 'test_value'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Invalid key')

    def test_get_nonexistent_cache_entry(self):
        """Test retrieving a non-existent cache entry"""
        cache_key = 'nonexistent_key'
        response = self.client.get(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Cache entry not found')

    def test_bulk_add_cache_entries(self):
        """Test adding multiple cache entries at once"""
        entries = [{'key': f'key{i}', 'value': f'value{i}'} for i in range(10)]
        response = self.client.post(f"{self.base_url}/cache/bulk", json={'entries': entries})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'Bulk entries added successfully')

    def test_bulk_get_cache_entries(self):
        """Test retrieving multiple cache entries at once"""
        keys = [f'key{i}' for i in range(10)]
        response = self.client.post(f"{self.base_url}/cache/bulk-get", json={'keys': keys})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['entries']), 10)

    def test_cache_eviction_policy(self):
        """Test the eviction policy"""
        for i in range(20): 
            self.client.post(f"{self.base_url}/cache", json={
                'key': f'key{i}',
                'value': f'value{i}'
            })
        # Oldest entries should be evicted
        response = self.client.get(f"{self.base_url}/cache/key0")
        self.assertEqual(response.status_code, 404)

    def test_cache_persistence(self):
        """Test if cache data persists after server restart"""
        cache_key = 'persistent_key'
        cache_value = 'persistent_value'
        self.client.post(f"{self.base_url}/cache", json={
            'key': cache_key,
            'value': cache_value
        })
        # Simulate server restart
        app.restart() 
        response = self.client.get(f"{self.base_url}/cache/{cache_key}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['value'], cache_value)

    def test_cache_clear(self):
        """Test clearing the entire cache"""
        self.client.post(f"{self.base_url}/cache", json={
            'key': 'key_to_clear',
            'value': 'value_to_clear'
        })
        response = self.client.delete(f"{self.base_url}/cache")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Cache cleared successfully')
        # Verify that cache is empty
        response = self.client.get(f"{self.base_url}/cache/key_to_clear")
        self.assertEqual(response.status_code, 404)

    def test_api_rate_limiting(self):
        """Test if API rate limiting is enforced"""
        for _ in range(100): 
            self.client.get(f"{self.base_url}/health")
        response = self.client.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json['error'], 'Rate limit exceeded')

    def test_admin_api_access(self):
        """Test if admin-only API endpoints require authentication"""
        response = self.client.get(f"{self.base_url}/admin/stats")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'Authentication required')

    def test_admin_api_access_with_token(self):
        """Test accessing admin API with valid token"""
        admin_token = "valid_admin_token"
        response = self.client.get(f"{self.base_url}/admin/stats", headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('cache_size', response.json)

    def test_cache_metrics_endpoint(self):
        """Test if cache metrics endpoint returns proper statistics"""
        response = self.client.get(f"{self.base_url}/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn('cache_hits', response.json)
        self.assertIn('cache_misses', response.json)

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        requests.delete(f"{cls.base_url}/cache")  # Clear the cache after tests


if __name__ == "__main__":
    unittest.main()