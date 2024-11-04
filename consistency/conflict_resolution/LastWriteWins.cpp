#include <iostream>
#include <unordered_map>
#include <string>
#include <chrono>
#include <mutex>
#include <thread>

using namespace std;
using namespace std::chrono;

class LastWriteWinsCache {
private:
    struct CacheValue {
        string value;
        system_clock::time_point timestamp;
    };

    unordered_map<string, CacheValue> cache;
    mutex cache_mutex;

public:
    // Insert or update a key-value pair with the current timestamp
    void put(const string& key, const string& value) {
        lock_guard<mutex> lock(cache_mutex);
        system_clock::time_point now = system_clock::now();

        if (cache.find(key) == cache.end()) {
            cache[key] = {value, now};
            cout << "Key inserted: " << key << " -> " << value << endl;
        } else {
            CacheValue& currentValue = cache[key];
            if (now > currentValue.timestamp) {
                currentValue.value = value;
                currentValue.timestamp = now;
                cout << "Key updated: " << key << " -> " << value << endl;
            }
        }
    }

    // Retrieve a value based on the key
    string get(const string& key) {
        lock_guard<mutex> lock(cache_mutex);
        if (cache.find(key) != cache.end()) {
            return cache[key].value;
        }
        return "Key not found";
    }

    // Simulate conflict resolution between two nodes
    void resolve_conflict(const string& key, const string& incoming_value, const system_clock::time_point& incoming_timestamp) {
        lock_guard<mutex> lock(cache_mutex);

        if (cache.find(key) == cache.end() || incoming_timestamp > cache[key].timestamp) {
            cache[key] = {incoming_value, incoming_timestamp};
            cout << "Conflict resolved, updated key: " << key << " -> " << incoming_value << endl;
        } else {
            cout << "Conflict resolved, kept existing key: " << key << " -> " << cache[key].value << endl;
        }
    }

    // Display the contents of the cache
    void display_cache() {
        lock_guard<mutex> lock(cache_mutex);
        for (const auto& entry : cache) {
            cout << "Key: " << entry.first << ", Value: " << entry.second.value
                 << ", Timestamp: " << duration_cast<milliseconds>(entry.second.timestamp.time_since_epoch()).count() << endl;
        }
    }
};

// Helper function to simulate writes from different nodes
void simulate_write(LastWriteWinsCache& cache, const string& key, const string& value, int delay) {
    this_thread::sleep_for(milliseconds(delay));
    cache.put(key, value);
}

void simulate_conflict_resolution(LastWriteWinsCache& cache, const string& key, const string& value, system_clock::time_point timestamp) {
    this_thread::sleep_for(milliseconds(100));
    cache.resolve_conflict(key, value, timestamp);
}

int main() {
    LastWriteWinsCache cache;

    // Simulating writes from different nodes
    thread t1(simulate_write, ref(cache), "key1", "value1", 100);
    thread t2(simulate_write, ref(cache), "key1", "value2", 200);

    t1.join();
    t2.join();

    cache.display_cache();

    // Simulate conflict resolution
    system_clock::time_point future_timestamp = system_clock::now() + seconds(5);
    simulate_conflict_resolution(cache, "key1", "conflict_value", future_timestamp);

    cache.display_cache();

    return 0;
}