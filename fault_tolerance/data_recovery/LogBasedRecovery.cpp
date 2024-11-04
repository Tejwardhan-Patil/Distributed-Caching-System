#include <iostream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <mutex>
#include <vector>

// Mutex to ensure thread-safe operations
std::mutex log_mutex;

// Log record structure
struct LogRecord {
    int transactionId;
    std::string operation;
    std::string key;
    std::string value;
};

// A class for managing Write-Ahead Logs (WAL)
class WriteAheadLog {
private:
    std::ofstream log_file;
    std::vector<LogRecord> log_buffer;
    const std::string log_file_path;

public:
    WriteAheadLog(const std::string &file_path) : log_file_path(file_path) {
        log_file.open(log_file_path, std::ios::app);
        if (!log_file.is_open()) {
            throw std::runtime_error("Unable to open log file.");
        }
    }

    ~WriteAheadLog() {
        log_file.close();
    }

    // Append a log record to the file
    void append_log(LogRecord record) {
        std::lock_guard<std::mutex> lock(log_mutex);
        log_file << record.transactionId << " " << record.operation << " " << record.key << " " << record.value << std::endl;
        log_buffer.push_back(record);
    }

    // Read log records from the file (for recovery purposes)
    std::vector<LogRecord> read_logs() {
        std::ifstream infile(log_file_path);
        std::vector<LogRecord> logs;
        LogRecord record;
        while (infile >> record.transactionId >> record.operation >> record.key >> record.value) {
            logs.push_back(record);
        }
        infile.close();
        return logs;
    }
};

// A in-memory cache structure
class InMemoryCache {
private:
    std::unordered_map<std::string, std::string> cache;
    WriteAheadLog wal;

public:
    InMemoryCache(const std::string &log_path) : wal(log_path) {}

    // Put data into cache with logging
    void put(int transactionId, const std::string &key, const std::string &value) {
        LogRecord log_record = {transactionId, "PUT", key, value};
        wal.append_log(log_record);
        cache[key] = value;
    }

    // Get data from cache
    std::string get(const std::string &key) {
        if (cache.find(key) != cache.end()) {
            return cache[key];
        }
        return "";
    }

    // Remove data from cache with logging
    void remove(int transactionId, const std::string &key) {
        LogRecord log_record = {transactionId, "REMOVE", key, ""};
        wal.append_log(log_record);
        cache.erase(key);
    }

    // Recover data from logs after a crash
    void recover() {
        std::vector<LogRecord> logs = wal.read_logs();
        for (const auto &record : logs) {
            if (record.operation == "PUT") {
                cache[record.key] = record.value;
            } else if (record.operation == "REMOVE") {
                cache.erase(record.key);
            }
        }
    }

    // Print cache state
    void print_cache() {
        std::lock_guard<std::mutex> lock(log_mutex);
        for (const auto &pair : cache) {
            std::cout << pair.first << ": " << pair.second << std::endl;
        }
    }
};

// A transaction manager to simulate transactions
class TransactionManager {
private:
    InMemoryCache &cache;
    int transaction_counter;

public:
    TransactionManager(InMemoryCache &cache_ref) : cache(cache_ref), transaction_counter(0) {}

    // Start a new transaction
    int start_transaction() {
        return ++transaction_counter;
    }

    // Commit a transaction with multiple operations
    void commit_transaction(int transactionId, const std::unordered_map<std::string, std::string> &operations) {
        for (const auto &op : operations) {
            cache.put(transactionId, op.first, op.second);
        }
    }

    // Simulate a failure and recovery
    void simulate_failure_and_recovery() {
        std::cout << "Simulating crash..." << std::endl;
        cache.recover();
        std::cout << "Recovery complete. Current cache state:" << std::endl;
        cache.print_cache();
    }
};

// Usage
int main() {
    // Initialize cache with log file
    InMemoryCache cache("cache_log.txt");
    TransactionManager transaction_manager(cache);

    // Simulate transactions
    int transactionId1 = transaction_manager.start_transaction();
    cache.put(transactionId1, "key1", "value1");
    cache.put(transactionId1, "key2", "value2");

    int transactionId2 = transaction_manager.start_transaction();
    cache.put(transactionId2, "key3", "value3");
    cache.remove(transactionId2, "key1");

    // Print current cache state
    std::cout << "Before recovery:" << std::endl;
    cache.print_cache();

    // Simulate a failure and recovery
    transaction_manager.simulate_failure_and_recovery();

    return 0;
}