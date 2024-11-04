import grpc
import time
from concurrent import futures
from cache_pb2 import CacheRequest, CacheResponse
from cache_pb2_grpc import CacheServiceServicer, add_CacheServiceServicer_to_server

class CacheServer(CacheServiceServicer):
    def __init__(self):
        self.cache = {}

    def GetCache(self, request, context):
        key = request.key
        if key in self.cache:
            return CacheResponse(value=self.cache[key], found=True)
        return CacheResponse(value='', found=False)

    def SetCache(self, request, context):
        key = request.key
        value = request.value
        self.cache[key] = value
        return CacheResponse(value=value, found=True)

    def DeleteCache(self, request, context):
        key = request.key
        if key in self.cache:
            del self.cache[key]
            return CacheResponse(value='', found=True)
        return CacheResponse(value='', found=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_CacheServiceServicer_to_server(CacheServer(), server)
    server.add_insecure_port('[::]:50051')
    print("Starting gRPC server on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("Stopping server...")
        server.stop(0)

if __name__ == '__main__':
    serve()

# Protobuf Definitions (cache.proto)
"""
syntax = "proto3";

service CacheService {
    rpc GetCache(CacheRequest) returns (CacheResponse);
    rpc SetCache(CacheRequest) returns (CacheResponse);
    rpc DeleteCache(CacheRequest) returns (CacheResponse);
}

message CacheRequest {
    string key = 1;
    string value = 2;
}

message CacheResponse {
    string value = 1;
    bool found = 2;
}
"""

# client.py
import grpc
from cache_pb2_grpc import CacheServiceStub
from cache_pb2 import CacheRequest

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = CacheServiceStub(channel)
        # Set key-value pair
        response = stub.SetCache(CacheRequest(key="name", value="Person"))
        print(f"Set: {response.value}, Found: {response.found}")

        # Get the value
        response = stub.GetCache(CacheRequest(key="name"))
        print(f"Get: {response.value}, Found: {response.found}")

        # Try to get a non-existing key
        response = stub.GetCache(CacheRequest(key="non_existing"))
        print(f"Get non-existing: {response.value}, Found: {response.found}")

        # Delete the key
        response = stub.DeleteCache(CacheRequest(key="name"))
        print(f"Delete: Found: {response.found}")

        # Try to get the deleted key
        response = stub.GetCache(CacheRequest(key="name"))
        print(f"Get after delete: {response.value}, Found: {response.found}")

if __name__ == '__main__':
    run()

# Unit Tests (test_grpc_protocol.py)
import unittest
from grpc_testing import server_from_dictionary, strict_real_time
from cache_pb2_grpc import CacheServiceStub
from cache_pb2 import CacheRequest, CacheResponse

class TestCacheServer(unittest.TestCase):
    def setUp(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        add_CacheServiceServicer_to_server(CacheServer(), self.server)
        self.server.start()

    def tearDown(self):
        self.server.stop(0)

    def test_set_cache(self):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = CacheServiceStub(channel)
            response = stub.SetCache(CacheRequest(key="key", value="value"))
            self.assertTrue(response.found)

    def test_get_cache(self):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = CacheServiceStub(channel)
            stub.SetCache(CacheRequest(key="key", value="value"))
            response = stub.GetCache(CacheRequest(key="key"))
            self.assertEqual(response.value, "value")
            self.assertTrue(response.found)

    def test_delete_cache(self):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = CacheServiceStub(channel)
            stub.SetCache(CacheRequest(key="key", value="value"))
            response = stub.DeleteCache(CacheRequest(key="key"))
            self.assertTrue(response.found)

    def test_get_cache_after_delete(self):
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = CacheServiceStub(channel)
            stub.SetCache(CacheRequest(key="key", value="value"))
            stub.DeleteCache(CacheRequest(key="key"))
            response = stub.GetCache(CacheRequest(key="key"))
            self.assertFalse(response.found)

if __name__ == '__main__':
    unittest.main()

# gRPC Interceptor for Logging (grpc_interceptor.py)
import grpc

class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method_name = handler_call_details.method
        print(f"Incoming request for method: {method_name}")
        return continuation(handler_call_details)

def serve_with_interceptor():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), interceptors=(LoggingInterceptor(),))
    add_CacheServiceServicer_to_server(CacheServer(), server)
    server.add_insecure_port('[::]:50051')
    print("Starting gRPC server with interceptor on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print("Stopping server...")
        server.stop(0)

if __name__ == '__main__':
    serve_with_interceptor()

# Prometheus Monitoring (monitoring.py)
from prometheus_client import start_http_server, Summary
import random
import time

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

@REQUEST_TIME.time()
def process_request(t):
    time.sleep(t)

if __name__ == '__main__':
    start_http_server(8000)
    while True:
        process_request(random.random())