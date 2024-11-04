#include <iostream>
#include <fstream>
#include <unordered_map>
#include <string>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <vector>
#include <queue>
#include <filesystem>

namespace fs = std::filesystem;

class SSDStore {
public:
    SSDStore(const std::string& dir, std::size_t cacheLimit);
    ~SSDStore();

    void put(const std::string& key, const std::string& value);
    std::string get(const std::string& key);
    void remove(const std::string& key);
    bool exists(const std::string& key);
    void persist();
    void loadCache();
    void evict();
    
private:
    std::unordered_map<std::string, std::string> cache_;
    std::queue<std::string> evictionQueue_;
    std::size_t cacheLimit_;
    std::string dirPath_;
    std::mutex mtx_;
    std::condition_variable cond_;
    bool stopEviction_ = false;

    std::string getFilePath(const std::string& key);
    void persistKeyValue(const std::string& key, const std::string& value);
    std::string loadFromFile(const std::string& key);
    void evictionThread();
    bool isCacheFull();
};

// Constructor
SSDStore::SSDStore(const std::string& dir, std::size_t cacheLimit)
    : dirPath_(dir), cacheLimit_(cacheLimit) {
    if (!fs::exists(dir)) {
        fs::create_directories(dir);
    }
    loadCache();
    std::thread(&SSDStore::evictionThread, this).detach();
}

// Destructor
SSDStore::~SSDStore() {
    std::unique_lock<std::mutex> lock(mtx_);
    stopEviction_ = true;
    cond_.notify_all();
}

void SSDStore::put(const std::string& key, const std::string& value) {
    std::lock_guard<std::mutex> lock(mtx_);
    cache_[key] = value;
    evictionQueue_.push(key);

    if (isCacheFull()) {
        evict();
    }
}

std::string SSDStore::get(const std::string& key) {
    std::lock_guard<std::mutex> lock(mtx_);
    if (cache_.find(key) != cache_.end()) {
        return cache_[key];
    }
    return loadFromFile(key);
}

void SSDStore::remove(const std::string& key) {
    std::lock_guard<std::mutex> lock(mtx_);
    cache_.erase(key);
    fs::remove(getFilePath(key));
}

bool SSDStore::exists(const std::string& key) {
    std::lock_guard<std::mutex> lock(mtx_);
    return cache_.find(key) != cache_.end() || fs::exists(getFilePath(key));
}

void SSDStore::persist() {
    std::lock_guard<std::mutex> lock(mtx_);
    for (const auto& entry : cache_) {
        persistKeyValue(entry.first, entry.second);
    }
}

void SSDStore::loadCache() {
    std::lock_guard<std::mutex> lock(mtx_);
    for (const auto& entry : fs::directory_iterator(dirPath_)) {
        std::string key = entry.path().stem().string();
        cache_[key] = loadFromFile(key);
        evictionQueue_.push(key);
    }
}

void SSDStore::evict() {
    while (isCacheFull()) {
        std::string key = evictionQueue_.front();
        evictionQueue_.pop();
        persistKeyValue(key, cache_[key]);
        cache_.erase(key);
    }
}

std::string SSDStore::getFilePath(const std::string& key) {
    return dirPath_ + "/" + key + ".cache";
}

void SSDStore::persistKeyValue(const std::string& key, const std::string& value) {
    std::ofstream ofs(getFilePath(key));
    if (ofs.is_open()) {
        ofs << value;
        ofs.close();
    }
}

std::string SSDStore::loadFromFile(const std::string& key) {
    std::ifstream ifs(getFilePath(key));
    std::string value;
    if (ifs.is_open()) {
        std::getline(ifs, value);
        ifs.close();
    }
    return value;
}

void SSDStore::evictionThread() {
    std::unique_lock<std::mutex> lock(mtx_);
    while (!stopEviction_) {
        cond_.wait_for(lock, std::chrono::seconds(5), [this] {
            return stopEviction_ || isCacheFull();
        });
        if (!stopEviction_) {
            evict();
        }
    }
}

bool SSDStore::isCacheFull() {
    return cache_.size() >= cacheLimit_;
}

// Testing the SSDStore implementation
int main() {
    SSDStore store("/tmp/ssd_cache", 5);

    store.put("key1", "value1");
    store.put("key2", "value2");
    store.put("key3", "value3");

    std::cout << "Value for key1: " << store.get("key1") << std::endl;
    std::cout << "Value for key2: " << store.get("key2") << std::endl;

    store.put("key4", "value4");
    store.put("key5", "value5");

    store.put("key6", "value6"); 

    std::cout << "Value for key1 after eviction: " << store.get("key1") << std::endl;

    store.persist();  

    return 0;
}