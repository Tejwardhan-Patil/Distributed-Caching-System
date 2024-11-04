import unittest
import subprocess
from unittest.mock import patch
from networking.protocols.GrpcProtocol import GrpcProtocol

class NetworkingTests(unittest.TestCase):

    def setUp(self):
        # Paths to the Java and C++ executables
        self.rpc_server_java = 'java -cp ./bin RPCServer'  # Java classpath for RPCServer
        self.rpc_client_cpp = './bin/RPCClient'  # C++ binary for RPCClient
        self.grpc_protocol = GrpcProtocol()

    def tearDown(self):
        # Clean up resources after tests
        pass

    def run_java_command(self, command):
        """Utility function to run Java command and capture output"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return None, str(e)

    def run_cpp_command(self, command):
        """Utility function to run C++ command and capture output"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return None, str(e)

    def test_rpc_server_start(self):
        """Test starting the Java RPCServer"""
        command = f"{self.rpc_server_java} start"
        stdout, stderr = self.run_java_command(command)
        self.assertIn("Server started", stdout)
        self.assertEqual(stderr, "")

    def test_rpc_server_stop(self):
        """Test stopping the Java RPCServer"""
        command = f"{self.rpc_server_java} stop"
        stdout, stderr = self.run_java_command(command)
        self.assertIn("Server stopped", stdout)
        self.assertEqual(stderr, "")

    def test_rpc_client_send_request(self):
        """Test sending a request using C++ RPCClient"""
        command = f"{self.rpc_client_cpp} send_request test_payload"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Request sent", stdout)
        self.assertEqual(stderr, "")

    def test_rpc_client_receive_response(self):
        """Test receiving a response using C++ RPCClient"""
        command = f"{self.rpc_client_cpp} receive_response"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Response received", stdout)
        self.assertEqual(stderr, "")

    @patch('networking.protocols.GrpcProtocol.send_message')
    def test_grpc_protocol_send_message(self, mock_send_message):
        """Test sending message using GrpcProtocol"""
        mock_send_message.return_value = 'message_sent'
        result = self.grpc_protocol.send_message('test_message')
        self.assertEqual(result, 'message_sent')
        mock_send_message.assert_called_once_with('test_message')

    @patch('networking.protocols.GrpcProtocol.receive_message')
    def test_grpc_protocol_receive_message(self, mock_receive_message):
        """Test receiving a message using GrpcProtocol"""
        mock_receive_message.return_value = 'test_message'
        message = self.grpc_protocol.receive_message()
        self.assertEqual(message, 'test_message')
        mock_receive_message.assert_called_once()

    def test_rpc_client_error_handling(self):
        """Test error handling for C++ RPCClient"""
        command = f"{self.rpc_client_cpp} send_request invalid_payload"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Error", stderr)

    def test_rpc_server_initialization(self):
        """Test if the Java RPCServer is initialized correctly"""
        command = f"{self.rpc_server_java} status"
        stdout, stderr = self.run_java_command(command)
        self.assertIn("Server running", stdout)
        self.assertEqual(stderr, "")

    def test_rpc_client_initialization(self):
        """Test if the C++ RPCClient is initialized correctly"""
        command = f"{self.rpc_client_cpp} status"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Client ready", stdout)
        self.assertEqual(stderr, "")

    def test_grpc_protocol_initialization(self):
        """Test if GrpcProtocol is initialized correctly"""
        self.assertIsInstance(self.grpc_protocol, GrpcProtocol)

    def test_rpc_client_timeout(self):
        """Test if C++ RPCClient handles timeout"""
        command = f"{self.rpc_client_cpp} send_request test_payload --timeout"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Timeout", stderr)

    def test_grpc_protocol_message_format(self):
        """Test if gRPC protocol formats the message correctly"""
        message = self.grpc_protocol.format_message('key', 'value')
        self.assertEqual(message, {'key': 'value'})

    def test_rpc_server_handle_multiple_requests(self):
        """Simulate multiple requests to the Java RPCServer"""
        command1 = f"{self.rpc_server_java} receive_request POST data1"
        command2 = f"{self.rpc_server_java} receive_request GET data2"
        stdout1, stderr1 = self.run_java_command(command1)
        stdout2, stderr2 = self.run_java_command(command2)

        self.assertIn("Request received", stdout1)
        self.assertIn("Request received", stdout2)

    def test_rpc_client_large_payload(self):
        """Test sending a large payload using the C++ RPCClient"""
        large_payload = 'x' * 10000  # 10k payload
        command = f"{self.rpc_client_cpp} send_request {large_payload}"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Request sent", stdout)
        self.assertEqual(stderr, "")

    def test_grpc_protocol_large_message(self):
        """Test sending a large message using GrpcProtocol"""
        large_message = 'y' * 10000  # 10k message
        result = self.grpc_protocol.send_message(large_message)
        self.assertEqual(result, 'message_sent')

    def test_rpc_client_disconnect(self):
        """Test disconnecting the C++ RPCClient"""
        command = f"{self.rpc_client_cpp} disconnect"
        stdout, stderr = self.run_cpp_command(command)
        self.assertIn("Client disconnected", stdout)
        self.assertEqual(stderr, "")

if __name__ == '__main__':
    unittest.main()