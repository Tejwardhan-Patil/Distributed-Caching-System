#include <iostream>
#include <unordered_map>
#include <queue>
#include <stdexcept>

class FIFOCache {
public:
    FIFOCache(size_t capacity) : capacity(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("Cache capacity must be greater than 0");
        }
    }

    // Retrieve a value from the cache
    int get(int key) {
        if (cacheMap.find(key) == cacheMap.end()) {
            return -1;  // Key not found
        }
        return cacheMap[key];  
    }

    // Add or update a value in the cache
    void put(int key, int value) {
        if (cacheMap.find(key) == cacheMap.end()) {
            if (cacheQueue.size() == capacity) {
                evict();
            }
            cacheQueue.push(key);  
        }
        cacheMap[key] = value;  
    }

    // Remove the oldest entry (FIFO policy)
    void evict() {
        int keyToRemove = cacheQueue.front();  
        cacheQueue.pop();                    
        cacheMap.erase(keyToRemove);          
    }

    // Check if the cache is empty
    bool isEmpty() const {
        return cacheQueue.empty();
    }

    // Clear all entries from the cache
    void clear() {
        while (!cacheQueue.empty()) {
            cacheQueue.pop();
        }
        cacheMap.clear();
    }

private:
    size_t capacity;                          // Maximum cache size
    std::unordered_map<int, int> cacheMap;    // Key-value map for cache entries
    std::queue<int> cacheQueue;               // Queue to track insertion order (FIFO)
};

// Main function to test the FIFO cache policy
int main() {
    size_t capacity = 3;
    FIFOCache cache(capacity);

    // Insert items into the cache
    cache.put(1, 10);
    cache.put(2, 20);
    cache.put(3, 30);

    // Accessing the cache
    std::cout << "Value for key 1: " << cache.get(1) << std::endl; 

    // Adding a new entry will trigger eviction (FIFO)
    cache.put(4, 40);
    std::cout << "Value for key 1 (after eviction): " << cache.get(1) << std::endl;  

    // Continue accessing other keys
    std::cout << "Value for key 2: " << cache.get(2) << std::endl;  
    std::cout << "Value for key 3: " << cache.get(3) << std::endl;  
    std::cout << "Value for key 4: " << cache.get(4) << std::endl;  

    // Insert more items and test evictions
    cache.put(5, 50);  // Evicts key 2
    std::cout << "Value for key 2 (after eviction): " << cache.get(2) << std::endl;  

    cache.put(6, 60);  // Evicts key 3
    std::cout << "Value for key 3 (after eviction): " << cache.get(3) << std::endl;  
    std::cout << "Value for key 4: " << cache.get(4) << std::endl;  
    std::cout << "Value for key 5: " << cache.get(5) << std::endl;  
    std::cout << "Value for key 6: " << cache.get(6) << std::endl;  

    // Clear the cache and confirm it is empty
    cache.clear();
    std::cout << "Cache is empty: " << (cache.isEmpty() ? "Yes" : "No") << std::endl;

    return 0;
}