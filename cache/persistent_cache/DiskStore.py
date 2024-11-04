import os
import pickle
import threading
from hashlib import sha256
from typing import Any

class DiskStore:
    def __init__(self, cache_dir: str, max_cache_size: int = 100 * 1024 * 1024):
        self.cache_dir = cache_dir
        self.max_cache_size = max_cache_size
        self.lock = threading.Lock()

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_file_path(self, key: str) -> str:
        hashed_key = sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.cache")

    def _evict_if_needed(self):
        """Evict cache entries if total size exceeds the maximum cache size."""
        total_size = sum(
            os.path.getsize(os.path.join(self.cache_dir, f)) for f in os.listdir(self.cache_dir)
        )
        if total_size > self.max_cache_size:
            self._evict()

    def _evict(self):
        """Evict the least recently accessed files to free space."""
        files = [(f, os.path.getctime(os.path.join(self.cache_dir, f))) for f in os.listdir(self.cache_dir)]
        files.sort(key=lambda x: x[1])  # Sort by creation time (oldest first)

        for file, _ in files:
            file_path = os.path.join(self.cache_dir, file)
            os.remove(file_path)
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) for f in os.listdir(self.cache_dir)
            )
            if total_size <= self.max_cache_size:
                break

    def set(self, key: str, value: Any) -> None:
        """Store an item in the cache."""
        with self.lock:
            self._evict_if_needed()

            cache_file_path = self._get_cache_file_path(key)
            with open(cache_file_path, "wb") as cache_file:
                pickle.dump(value, cache_file)

    def get(self, key: str) -> Any:
        """Retrieve an item from the cache."""
        cache_file_path = self._get_cache_file_path(key)

        if not os.path.exists(cache_file_path):
            return None

        with open(cache_file_path, "rb") as cache_file:
            return pickle.load(cache_file)

    def delete(self, key: str) -> None:
        """Remove an item from the cache."""
        with self.lock:
            cache_file_path = self._get_cache_file_path(key)

            if os.path.exists(cache_file_path):
                os.remove(cache_file_path)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            for file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file)
                os.remove(file_path)

    def cache_size(self) -> int:
        """Return the total size of the cache."""
        return sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in os.listdir(self.cache_dir))

    def cache_entries(self) -> int:
        """Return the total number of entries in the cache."""
        return len(os.listdir(self.cache_dir))

    def _read_cache_metadata(self):
        """Read metadata like cache size or entries for advanced cache strategies."""
        return {
            "size": self.cache_size(),
            "entries": self.cache_entries(),
        }


class PersistentCache:
    def __init__(self, cache_dir: str, max_cache_size: int = 100 * 1024 * 1024):
        self.store = DiskStore(cache_dir, max_cache_size)

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair in the cache."""
        self.store.set(key, value)

    def get(self, key: str) -> Any:
        """Retrieve a value by key from the cache."""
        return self.store.get(key)

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        self.store.delete(key)

    def clear_cache(self) -> None:
        """Clear the entire cache."""
        self.store.clear()

    def cache_status(self) -> str:
        """Return a summary of the cache status."""
        metadata = self.store._read_cache_metadata()
        return f"Cache contains {metadata['entries']} entries using {metadata['size']} bytes."


# Usage
if __name__ == "__main__":
    # Define cache directory and size (50MB)
    cache_dir = "./disk_cache"
    max_cache_size = 50 * 1024 * 1024  # 50 MB

    # Initialize PersistentCache
    persistent_cache = PersistentCache(cache_dir, max_cache_size)

    # Set some cache values
    persistent_cache.set("user:1234", {"name": "Person", "email": "person@website.com"})
    persistent_cache.set("session:5678", {"session_id": "abcd1234", "status": "active"})

    # Retrieve cache values
    user_info = persistent_cache.get("user:1234")
    print(f"Retrieved user info: {user_info}")

    session_info = persistent_cache.get("session:5678")
    print(f"Retrieved session info: {session_info}")

    # Cache status
    print(persistent_cache.cache_status())

    # Delete cache entry
    persistent_cache.delete("session:5678")
    print(f"Session entry deleted. Cache status: {persistent_cache.cache_status()}")

    # Clear the entire cache
    persistent_cache.clear_cache()
    print("Cache cleared.")
    print(persistent_cache.cache_status())