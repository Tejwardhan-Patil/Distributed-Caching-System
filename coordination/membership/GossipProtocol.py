import random
import threading
import time
import socket
import json

class GossipProtocol:
    def __init__(self, node_id, known_nodes, gossip_interval=1, failure_detection_timeout=5):
        self.node_id = node_id
        self.known_nodes = known_nodes
        self.gossip_interval = gossip_interval
        self.failure_detection_timeout = failure_detection_timeout
        self.membership_list = {node_id: {'status': 'alive', 'timestamp': time.time()}}
        self.lock = threading.Lock()

    def start(self):
        gossip_thread = threading.Thread(target=self.gossip_loop)
        failure_detection_thread = threading.Thread(target=self.failure_detection_loop)
        gossip_thread.start()
        failure_detection_thread.start()

    def gossip_loop(self):
        while True:
            time.sleep(self.gossip_interval)
            self.gossip()

    def gossip(self):
        with self.lock:
            nodes_to_gossip = random.sample(self.known_nodes, min(len(self.known_nodes), 3))
            for node in nodes_to_gossip:
                try:
                    self.send_gossip(node)
                except Exception as e:
                    print(f"Failed to send gossip to {node}: {e}")

    def send_gossip(self, target_node):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            gossip_data = json.dumps(self.membership_list).encode('utf-8')
            s.sendto(gossip_data, (target_node, 5000))

    def receive_gossip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', 5000))
            while True:
                data, addr = s.recvfrom(1024)
                received_membership_list = json.loads(data.decode('utf-8'))
                self.merge_membership_list(received_membership_list)

    def merge_membership_list(self, received_list):
        with self.lock:
            for node, metadata in received_list.items():
                if node not in self.membership_list or metadata['timestamp'] > self.membership_list[node]['timestamp']:
                    self.membership_list[node] = metadata

    def failure_detection_loop(self):
        while True:
            time.sleep(self.gossip_interval)
            self.check_for_failures()

    def check_for_failures(self):
        current_time = time.time()
        with self.lock:
            for node, metadata in self.membership_list.items():
                if metadata['status'] == 'alive' and current_time - metadata['timestamp'] > self.failure_detection_timeout:
                    print(f"Node {node} failed")
                    self.membership_list[node]['status'] = 'failed'

    def update_membership(self, node, status):
        with self.lock:
            self.membership_list[node] = {'status': status, 'timestamp': time.time()}

    def join_network(self):
        # Attempt to join the gossip network
        for node in self.known_nodes:
            try:
                self.send_gossip(node)
                print(f"Sent join request to {node}")
            except Exception as e:
                print(f"Failed to send join request to {node}: {e}")

if __name__ == "__main__":
    node_id = f"node-{random.randint(1, 1000)}"
    known_nodes = ["127.0.0.1"]  
    gossip_protocol = GossipProtocol(node_id, known_nodes)
    
    # Start receiving gossip in a separate thread
    receive_thread = threading.Thread(target=gossip_protocol.receive_gossip)
    receive_thread.start()

    gossip_protocol.join_network()
    gossip_protocol.start()