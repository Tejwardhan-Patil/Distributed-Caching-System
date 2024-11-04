import json
import os
from typing import Any

class JsonSerializer:
    def __init__(self, cache_dir: str = "./cache"):
        """
        Initialize the JSON serializer with a specified cache directory.
        """
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def serialize(self, data: Any, file_name: str) -> None:
        """
        Serializes Python objects to a JSON file and stores it in the cache directory.
        """
        file_path = os.path.join(self.cache_dir, f"{file_name}.json")
        try:
            with open(file_path, "w") as json_file:
                json.dump(data, json_file)
        except (OSError, IOError) as e:
            raise Exception(f"Failed to write JSON data to file: {e}")

    def deserialize(self, file_name: str) -> Any:
        """
        Deserializes JSON data from a file in the cache directory and returns the corresponding Python object.
        """
        file_path = os.path.join(self.cache_dir, f"{file_name}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cache file {file_name}.json not found.")
        try:
            with open(file_path, "r") as json_file:
                return json.load(json_file)
        except (OSError, IOError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to read JSON data from file: {e}")

    def exists(self, file_name: str) -> bool:
        """
        Checks if a cache file exists in the cache directory.
        """
        file_path = os.path.join(self.cache_dir, f"{file_name}.json")
        return os.path.exists(file_path)

    def delete(self, file_name: str) -> None:
        """
        Deletes a cache file from the cache directory.
        """
        file_path = os.path.join(self.cache_dir, f"{file_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"Cache file {file_name}.json not found for deletion.")

class CacheManager:
    def __init__(self, max_cache_size: int = 100):
        """
        Manages the cache for serialized JSON objects. Implements a basic eviction policy
        when cache size exceeds the max_cache_size.
        """
        self.serializer = JsonSerializer()
        self.max_cache_size = max_cache_size
        self.cache_index = []
        self.cache_size = 0

    def _evict_if_needed(self) -> None:
        """
        Evicts the oldest cache file if the cache size exceeds the maximum limit.
        """
        if self.cache_size >= self.max_cache_size:
            oldest_file = self.cache_index.pop(0)
            self.serializer.delete(oldest_file)
            self.cache_size -= 1

    def cache(self, data: Any, file_name: str) -> None:
        """
        Caches serialized JSON data and applies eviction policy when necessary.
        """
        if self.serializer.exists(file_name):
            self.serializer.delete(file_name)
            self.cache_index.remove(file_name)
            self.cache_size -= 1

        self._evict_if_needed()
        self.serializer.serialize(data, file_name)
        self.cache_index.append(file_name)
        self.cache_size += 1

    def retrieve(self, file_name: str) -> Any:
        """
        Retrieves cached JSON data if available; otherwise raises an exception.
        """
        if self.serializer.exists(file_name):
            return self.serializer.deserialize(file_name)
        raise FileNotFoundError(f"Cache file {file_name} not found.")

    def clear_cache(self) -> None:
        """
        Clears all the cache by deleting every cached JSON file.
        """
        for file_name in self.cache_index:
            self.serializer.delete(file_name)
        self.cache_index.clear()
        self.cache_size = 0

class CacheLRUPolicy(CacheManager):
    def __init__(self, max_cache_size: int = 100):
        """
        Manages the cache with an LRU (Least Recently Used) eviction policy. 
        """
        super().__init__(max_cache_size)
        self.cache_access_order = {}

    def cache(self, data: Any, file_name: str) -> None:
        """
        Caches data and updates access order to maintain LRU eviction policy.
        """
        self._update_access(file_name)
        super().cache(data, file_name)

    def retrieve(self, file_name: str) -> Any:
        """
        Retrieves cached data and updates access order to maintain LRU eviction policy.
        """
        self._update_access(file_name)
        return super().retrieve(file_name)

    def _update_access(self, file_name: str) -> None:
        """
        Updates the access order of the cached files to track the most recently used items.
        """
        if file_name in self.cache_access_order:
            self.cache_access_order.pop(file_name)
        self.cache_access_order[file_name] = None 

    def _evict_if_needed(self) -> None:
        """
        Evicts the least recently used cache file if the cache size exceeds the maximum limit.
        """
        if self.cache_size >= self.max_cache_size:
            lru_file = next(iter(self.cache_access_order))
            self.cache_access_order.pop(lru_file)
            self.cache_index.remove(lru_file)
            self.serializer.delete(lru_file)
            self.cache_size -= 1

if __name__ == "__main__":
    cache = CacheLRUPolicy(max_cache_size=10)
    
    # Caching operations
    sample_data = {"key": "value"}
    
    for i in range(15):
        cache.cache(sample_data, f"cache_file_{i}")
    
    # Retrieve data
    try:
        print(cache.retrieve("cache_file_5"))
    except FileNotFoundError:
        print("cache_file_5 not found.")