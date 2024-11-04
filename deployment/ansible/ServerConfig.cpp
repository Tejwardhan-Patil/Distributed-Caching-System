#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <algorithm> 

class ServerConfig {
private:
    std::string ansibleInventoryPath;
    std::string ansiblePlaybookPath;
    std::vector<std::string> serverIPs;

    int executeCommand(const std::string &command) {
        std::system(command.c_str());
        return 0;
    }

    void createInventoryFile() {
        std::ofstream inventoryFile(ansibleInventoryPath);
        if (!inventoryFile.is_open()) {
            std::cerr << "Error creating inventory file\n";
            return;
        }

        inventoryFile << "[cache_servers]\n";
        for (const auto &ip : serverIPs) {
            inventoryFile << ip << " ansible_ssh_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa\n";
        }
        inventoryFile.close();
    }

    void createPlaybookFile() {
        std::ofstream playbookFile(ansiblePlaybookPath);
        if (!playbookFile.is_open()) {
            std::cerr << "Error creating playbook file\n";
            return;
        }

        playbookFile << "---\n";
        playbookFile << "- hosts: cache_servers\n";
        playbookFile << "  become: yes\n";
        playbookFile << "  tasks:\n";
        playbookFile << "    - name: Update and upgrade apt packages\n";
        playbookFile << "      apt:\n";
        playbookFile << "        update_cache: yes\n";
        playbookFile << "        upgrade: dist\n";
        playbookFile << "\n";
        playbookFile << "    - name: Install necessary dependencies\n";
        playbookFile << "      apt:\n";
        playbookFile << "        name:\n";
        playbookFile << "          - build-essential\n";
        playbookFile << "          - cmake\n";
        playbookFile << "          - git\n";
        playbookFile << "        state: present\n";
        playbookFile << "\n";
        playbookFile << "    - name: Setup distributed cache software\n";
        playbookFile << "      git:\n";
        playbookFile << "        repo: 'https://github.com/repo/distributed-cache.git'\n";
        playbookFile << "        dest: '/opt/distributed-cache'\n";
        playbookFile << "        version: 'main'\n";
        playbookFile << "\n";
        playbookFile << "    - name: Build and install cache software\n";
        playbookFile << "      shell: |\n";
        playbookFile << "        cd /opt/distributed-cache\n";
        playbookFile << "        mkdir build\n";
        playbookFile << "        cd build\n";
        playbookFile << "        cmake ..\n";
        playbookFile << "        make\n";
        playbookFile << "        make install\n";
        playbookFile << "\n";
        playbookFile << "    - name: Configure systemd service for cache\n";
        playbookFile << "      copy:\n";
        playbookFile << "        content: |\n";
        playbookFile << "          [Unit]\n";
        playbookFile << "          Description=Distributed Cache Service\n";
        playbookFile << "          After=network.target\n";
        playbookFile << "\n";
        playbookFile << "          [Service]\n";
        playbookFile << "          ExecStart=/usr/local/bin/distributed_cache\n";
        playbookFile << "          Restart=always\n";
        playbookFile << "\n";
        playbookFile << "          [Install]\n";
        playbookFile << "          WantedBy=multi-user.target\n";
        playbookFile << "        dest: /systemd/system/distributed_cache.service\n";
        playbookFile << "\n";
        playbookFile << "    - name: Enable and start cache service\n";
        playbookFile << "      systemd:\n";
        playbookFile << "        name: distributed_cache.service\n";
        playbookFile << "        enabled: yes\n";
        playbookFile << "        state: started\n";
        playbookFile << "\n";
        playbookFile << "    - name: Verify cache service is running\n";
        playbookFile << "      shell: systemctl status distributed_cache\n";
        playbookFile << "\n";
        playbookFile.close();
    }

public:
    ServerConfig(const std::string &inventoryPath, const std::string &playbookPath, const std::vector<std::string> &ips)
        : ansibleInventoryPath(inventoryPath), ansiblePlaybookPath(playbookPath), serverIPs(ips) {}

    void deployServers() {
        createInventoryFile();
        createPlaybookFile();

        std::cout << "Running Ansible playbook...\n";
        std::string command = "ansible-playbook -i " + ansibleInventoryPath + " " + ansiblePlaybookPath;
        if (executeCommand(command) == 0) {
            std::cout << "Deployment successful\n";
        } else {
            std::cerr << "Deployment failed\n";
        }
    }

    // Corrected function to remove server
    void removeServer(const std::string &ip) {
        auto it = std::remove(serverIPs.begin(), serverIPs.end(), ip);
        if (it != serverIPs.end()) {
            serverIPs.erase(it, serverIPs.end());
        } else {
            std::cerr << "Server IP not found\n";
        }
    }

    void addServer(const std::string &ip) {
        serverIPs.push_back(ip);
    }

    void displayServers() const {
        std::cout << "Current servers in the inventory:\n";
        for (const auto &ip : serverIPs) {
            std::cout << "- " << ip << "\n";
        }
    }
};

int main() {
    std::vector<std::string> servers = {
        "192.168.1.10", "192.168.1.11", "192.168.1.12"
    };

    std::string inventoryPath = "/deployment/ansible/hosts";
    std::string playbookPath = "/deployment/ansible/playbook.yml";

    ServerConfig config(inventoryPath, playbookPath, servers);

    config.displayServers();
    config.deployServers();

    return 0;
}