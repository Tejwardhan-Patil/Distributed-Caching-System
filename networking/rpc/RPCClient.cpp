#include <iostream>
#include <string>
#include <memory>
#include <stdexcept>
#include <grpcpp/grpcpp.h>
#include "rpc_service.grpc.pb.h"

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using rpc::RPCRequest;
using rpc::RPCResponse;
using rpc::RPCService;

class RPCClient {
public:
    RPCClient(std::shared_ptr<Channel> channel) 
        : stub_(RPCService::NewStub(channel)) {}

    // Function to send a request to the RPC server and receive a response
    std::string SendRPCRequest(const std::string& request_data) {
        // Creating and populating the request object
        RPCRequest request;
        request.set_data(request_data);

        // Response object to receive data from the server
        RPCResponse response;

        // Context for the client to allow customization of RPC behaviors
        ClientContext context;

        // Make RPC call to the server
        Status status = stub_->ProcessRequest(&context, request, &response);

        // Error handling
        if (status.ok()) {
            return response.data();
        } else {
            std::cerr << "RPC failed: " << status.error_message() << std::endl;
            throw std::runtime_error("RPC Request failed");
        }
    }

    // Function to establish a connection to the server
    bool ConnectToServer(const std::string& server_address) {
        try {
            stub_ = RPCService::NewStub(grpc::CreateChannel(server_address, grpc::InsecureChannelCredentials()));
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Error connecting to server: " << e.what() << std::endl;
            return false;
        }
    }

    // Ping the server to check if it is alive
    bool PingServer() {
        RPCRequest ping_request;
        ping_request.set_data("ping");

        RPCResponse response;
        ClientContext context;

        Status status = stub_->ProcessRequest(&context, ping_request, &response);

        if (status.ok() && response.data() == "pong") {
            std::cout << "Server is alive!" << std::endl;
            return true;
        } else {
            std::cerr << "Server is down!" << std::endl;
            return false;
        }
    }

private:
    std::unique_ptr<RPCService::Stub> stub_;
};

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <server_address>" << std::endl;
        return -1;
    }

    std::string server_address = argv[1];

    RPCClient client(grpc::CreateChannel(server_address, grpc::InsecureChannelCredentials()));

    if (!client.ConnectToServer(server_address)) {
        std::cerr << "Failed to connect to server at " << server_address << std::endl;
        return -1;
    }

    if (!client.PingServer()) {
        std::cerr << "Server is not responding!" << std::endl;
        return -1;
    }

    // Test sending an RPC request
    try {
        std::string request_data = "Hello, Server!";
        std::string response = client.SendRPCRequest(request_data);
        std::cout << "Server Response: " << response << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Exception during RPC: " << e.what() << std::endl;
        return -1;
    }

    return 0;
}