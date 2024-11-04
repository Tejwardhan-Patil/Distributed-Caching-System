#include <iostream>
#include <unordered_map>
#include <list>
#include <string>
#include <chrono>
#include <stdexcept>
#include <mutex>

class InMemoryStore {
private:
    // Node to store key-value pairs
    struct CacheNode {
        std::string key;
        std::string value;
        std::chrono::steady_clock::time_point last_accessed;

        CacheNode(std::string k, std::string v) : key(k), value(v) {
            last_accessed = std::chrono::steady_clock::now();
        }
    };

    // Maximum size of the cache
    size_t max_size;
    // Mutex for thread-safety
    std::mutex cache_mutex;
    // Hashmap to store keys and their corresponding list iterators
    std::unordered_map<std::string, std::list<CacheNode>::iterator> cache_map;
    // List to maintain access order
    std::list<CacheNode> cache_list;

    // Private method to update node's access time and move to front
    void touchNode(std::list<CacheNode>::iterator node_itr) {
        node_itr->last_accessed = std::chrono::steady_clock::now();
        cache_list.splice(cache_list.begin(), cache_list, node_itr);
    }

    // Evict least recently used node when the cache is full
    void evictIfNecessary() {
        if (cache_list.size() > max_size) {
            auto node_to_evict = cache_list.back();
            cache_map.erase(node_to_evict.key);
            cache_list.pop_back();
        }
    }

public:
    // Constructor to initialize the cache with a specific size
    InMemoryStore(size_t size) : max_size(size) {
        if (size == 0) {
            throw std::invalid_argument("Cache size cannot be zero");
        }
    }

    // Insert or update a key-value pair in the cache
    void put(const std::string& key, const std::string& value) {
        std::lock_guard<std::mutex> lock(cache_mutex);

        auto found = cache_map.find(key);
        if (found != cache_map.end()) {
            // If key exists, update the value and move to front
            found->second->value = value;
            touchNode(found->second);
        } else {
            // If key does not exist, create a new node and insert
            cache_list.emplace_front(key, value);
            cache_map[key] = cache_list.begin();
        }

        // Evict if cache size exceeds the max size
        evictIfNecessary();
    }

    // Retrieve value by key
    std::string get(const std::string& key) {
        std::lock_guard<std::mutex> lock(cache_mutex);

        auto found = cache_map.find(key);
        if (found != cache_map.end()) {
            touchNode(found->second);
            return found->second->value;
        }

        throw std::runtime_error("Key not found in cache");
    }

    // Remove a key-value pair from the cache
    void remove(const std::string& key) {
        std::lock_guard<std::mutex> lock(cache_mutex);

        auto found = cache_map.find(key);
        if (found != cache_map.end()) {
            cache_list.erase(found->second);
            cache_map.erase(found);
        } else {
            throw std::runtime_error("Key not found for removal");
        }
    }

    // Check if key exists in the cache
    bool exists(const std::string& key) {
        std::lock_guard<std::mutex> lock(cache_mutex);
        return cache_map.find(key) != cache_map.end();
    }

    // Return current cache size
    size_t size() {
        std::lock_guard<std::mutex> lock(cache_mutex);
        return cache_list.size();
    }

    // Print the current state of the cache (for debugging)
    void printCache() {
        std::lock_guard<std::mutex> lock(cache_mutex);
        for (const auto& node : cache_list) {
            std::cout << "Key: " << node.key << " | Value: " << node.value << " | Last Accessed: "
                      << std::chrono::duration_cast<std::chrono::milliseconds>(
                             node.last_accessed.time_since_epoch()).count()
                      << " ms" << std::endl;
        }
    }

    // Clear all elements from the cache
    void clear() {
        std::lock_guard<std::mutex> lock(cache_mutex);
        cache_list.clear();
        cache_map.clear();
    }

    // Retrieve the least recently used key
    std::string getLRUKey() {
        std::lock_guard<std::mutex> lock(cache_mutex);
        if (cache_list.empty()) {
            throw std::runtime_error("Cache is empty");
        }
        return cache_list.back().key;
    }
};

// Usage
int main() {
    try {
        InMemoryStore cache(3);

        cache.put("key1", "value1");
        cache.put("key2", "value2");
        cache.put("key3", "value3");

        std::cout << "Cache after inserting 3 items:" << std::endl;
        cache.printCache();

        cache.put("key4", "value4");  // Evict key1
        std::cout << "\nCache after inserting key4 (key1 should be evicted):" << std::endl;
        cache.printCache();

        std::cout << "\nAccessing key2 (this should move it to the front):" << std::endl;
        cache.get("key2");
        cache.printCache();

        std::cout << "\nCache size: " << cache.size() << std::endl;

        std::cout << "\nRemoving key3" << std::endl;
        cache.remove("key3");
        cache.printCache();

        std::cout << "\nClearing cache..." << std::endl;
        cache.clear();
        cache.printCache();
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
    }

    return 0;
}