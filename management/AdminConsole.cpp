#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <mutex>
#include <chrono>
#include <json/json.h>
#include <httplib.h> 
#include "CacheManager.h" 
#include "MetricsManager.h" 
#include "ConfigManager.h" 

std::mutex consoleMutex;
CacheManager cacheManager;
MetricsManager metricsManager;
ConfigManager configManager;

// Function to handle node management
void handleNodes(const httplib::Request &req, httplib::Response &res) {
    std::lock_guard<std::mutex> lock(consoleMutex);
    if (req.method == "GET") {
        Json::Value nodes = cacheManager.listNodes();
        Json::StreamWriterBuilder writer;
        res.set_content(Json::writeString(writer, nodes), "application/json");
    } else if (req.method == "POST") {
        Json::CharReaderBuilder reader;
        Json::Value node;
        std::string errs;
        std::istringstream s(req.body);
        std::string newNodeId;
        if (Json::parseFromStream(reader, s, &node, &errs)) {
            newNodeId = cacheManager.addNode(node["ip"].asString(), node["port"].asInt());
            res.set_content("Node added: " + newNodeId, "text/plain");
        } else {
            res.status = 400;
            res.set_content("Invalid JSON format", "text/plain");
        }
    }
}

// Function to handle metrics
void handleMetrics(const httplib::Request &req, httplib::Response &res) {
    std::lock_guard<std::mutex> lock(consoleMutex);
    Json::Value metrics = metricsManager.collectMetrics();
    Json::StreamWriterBuilder writer;
    res.set_content(Json::writeString(writer, metrics), "application/json");
}

// Function to handle configuration settings
void handleConfig(const httplib::Request &req, httplib::Response &res) {
    std::lock_guard<std::mutex> lock(consoleMutex);
    if (req.method == "GET") {
        Json::Value config = configManager.getConfig();
        Json::StreamWriterBuilder writer;
        res.set_content(Json::writeString(writer, config), "application/json");
    } else if (req.method == "POST") {
        Json::CharReaderBuilder reader;
        Json::Value newConfig;
        std::string errs;
        std::istringstream s(req.body);
        if (Json::parseFromStream(reader, s, &newConfig, &errs)) {
            configManager.setConfig(newConfig);
            res.set_content("Configuration updated successfully", "text/plain");
        } else {
            res.status = 400;
            res.set_content("Invalid JSON format", "text/plain");
        }
    }
}

// Function to handle cache management (clear cache, update policies)
void handleCacheManagement(const httplib::Request &req, httplib::Response &res) {
    std::lock_guard<std::mutex> lock(consoleMutex);
    if (req.method == "POST") {
        if (req.matches.size() > 1 && req.matches[1] == "clear") {
            cacheManager.clearCache();
            res.set_content("Cache cleared successfully", "text/plain");
        } else if (req.matches.size() > 1 && req.matches[1] == "policy") {
            Json::CharReaderBuilder reader;
            Json::Value policy;
            std::string errs;
            std::istringstream s(req.body);
            if (Json::parseFromStream(reader, s, &policy, &errs)) {
                cacheManager.updateEvictionPolicy(policy["policy"].asString());
                res.set_content("Eviction policy updated", "text/plain");
            } else {
                res.status = 400;
                res.set_content("Invalid JSON format", "text/plain");
            }
        } else {
            res.status = 400;
            res.set_content("Invalid operation", "text/plain");
        }
    }
}

// Function to run the Admin Console server
void runAdminConsole(int port) {
    httplib::Server svr;

    svr.Get("/nodes", handleNodes);
    svr.Post("/nodes", handleNodes);
    svr.Get("/metrics", handleMetrics);
    svr.Get("/config", handleConfig);
    svr.Post("/config", handleConfig);
    svr.Post(R"(/cache/(.*))", handleCacheManagement);

    std::cout << "Admin Console is running on port " << port << std::endl;
    svr.listen("0.0.0.0", port);
}

int main(int argc, char* argv[]) {
    int port = 8080;
    if (argc > 1) {
        port = std::stoi(argv[1]);
    }

    std::thread adminThread(runAdminConsole, port);
    adminThread.detach();

    // Simulate ongoing admin tasks
    while (true) {
        std::this_thread::sleep_for(std::chrono::seconds(10));
    }

    return 0;
}