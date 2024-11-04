#include <iostream>
#include <fstream>
#include <string>
#include <json/json.h>

class GrafanaDashboard {
public:
    GrafanaDashboard(const std::string& dashboardName) : name(dashboardName) {
        dashboardConfig["dashboard"]["title"] = dashboardName;
        dashboardConfig["dashboard"]["panels"] = Json::Value(Json::arrayValue);
        setupTimeSettings();
    }

    void addGraphPanel(const std::string& title, const std::string& target, int x, int y, int width, int height) {
        Json::Value panel;
        panel["type"] = "graph";
        panel["title"] = title;
        panel["datasource"] = "Prometheus";
        panel["gridPos"]["x"] = x;
        panel["gridPos"]["y"] = y;
        panel["gridPos"]["w"] = width;
        panel["gridPos"]["h"] = height;

        Json::Value targets(Json::arrayValue);
        Json::Value query;
        query["expr"] = target;
        targets.append(query);
        panel["targets"] = targets;

        dashboardConfig["dashboard"]["panels"].append(panel);
    }

    void addStatPanel(const std::string& title, const std::string& target, int x, int y, int width, int height) {
        Json::Value panel;
        panel["type"] = "stat";
        panel["title"] = title;
        panel["datasource"] = "Prometheus";
        panel["gridPos"]["x"] = x;
        panel["gridPos"]["y"] = y;
        panel["gridPos"]["w"] = width;
        panel["gridPos"]["h"] = height;

        Json::Value targets(Json::arrayValue);
        Json::Value query;
        query["expr"] = target;
        targets.append(query);
        panel["targets"] = targets;

        dashboardConfig["dashboard"]["panels"].append(panel);
    }

    void saveToFile(const std::string& filePath) {
        std::ofstream file(filePath);
        if (!file.is_open()) {
            std::cerr << "Failed to open file: " << filePath << std::endl;
            return;
        }
        Json::StreamWriterBuilder writer;
        std::string outputConfig = Json::writeString(writer, dashboardConfig);
        file << outputConfig;
        file.close();
    }

private:
    std::string name;
    Json::Value dashboardConfig;

    void setupTimeSettings() {
        dashboardConfig["dashboard"]["time"]["from"] = "now-6h";
        dashboardConfig["dashboard"]["time"]["to"] = "now";
    }
};

int main() {
    // Create a Grafana dashboard
    GrafanaDashboard dashboard("Cache System Monitoring");

    // Adding Panels to the Dashboard
    dashboard.addGraphPanel("Cache Hit Rate", "cache_hit_rate", 0, 0, 12, 6);
    dashboard.addGraphPanel("Cache Miss Rate", "cache_miss_rate", 12, 0, 12, 6);
    dashboard.addStatPanel("Current Cache Size", "current_cache_size", 0, 6, 12, 4);
    dashboard.addStatPanel("Cache Evictions", "cache_evictions", 12, 6, 12, 4);

    // Save the dashboard configuration to a JSON file
    dashboard.saveToFile("grafana_dashboard_cache_system.json");

    std::cout << "Grafana dashboard configuration has been saved to grafana_dashboard_cache_system.json" << std::endl;
    return 0;
}