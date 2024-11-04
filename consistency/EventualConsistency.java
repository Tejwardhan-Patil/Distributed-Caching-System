package consistency;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.Queue;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;


public class EventualConsistency {

    private static class Node {
        private final String nodeId;
        private final Map<String, String> dataStore;
        private final Queue<Update> updateQueue;
        private final AtomicBoolean isSynced;

        public Node(String nodeId) {
            this.nodeId = nodeId;
            this.dataStore = new ConcurrentHashMap<>();
            this.updateQueue = new ConcurrentLinkedQueue<>();
            this.isSynced = new AtomicBoolean(true);
        }

        public String getNodeId() {
            return nodeId;
        }

        public void applyUpdate(Update update) {
            dataStore.put(update.getKey(), update.getValue());
            isSynced.set(false);
        }

        public void enqueueUpdate(Update update) {
            updateQueue.offer(update);
        }

        public boolean syncWith(Node otherNode) {
            for (Map.Entry<String, String> entry : dataStore.entrySet()) {
                if (!otherNode.dataStore.containsKey(entry.getKey()) ||
                        !otherNode.dataStore.get(entry.getKey()).equals(entry.getValue())) {
                    otherNode.applyUpdate(new Update(entry.getKey(), entry.getValue()));
                }
            }
            isSynced.set(true);
            return true;
        }

        public boolean isSynced() {
            return isSynced.get();
        }
    }

    private static class Update {
        private final String key;
        private final String value;

        public Update(String key, String value) {
            this.key = key;
            this.value = value;
        }

        public String getKey() {
            return key;
        }

        public String getValue() {
            return value;
        }
    }

    private final List<Node> nodes;
    private final ExecutorService executorService;

    public EventualConsistency(int numNodes) {
        this.nodes = new ArrayList<>();
        for (int i = 1; i <= numNodes; i++) {
            nodes.add(new Node("Node" + i));
        }
        this.executorService = Executors.newFixedThreadPool(numNodes);
    }

    public void updateNode(String nodeId, String key, String value) {
        Node node = getNodeById(nodeId);
        if (node != null) {
            Update update = new Update(key, value);
            node.applyUpdate(update);
            propagateUpdate(node, update);
        }
    }

    private Node getNodeById(String nodeId) {
        for (Node node : nodes) {
            if (node.getNodeId().equals(nodeId)) {
                return node;
            }
        }
        return null;
    }

    private void propagateUpdate(Node originNode, Update update) {
        originNode.enqueueUpdate(update);
        for (Node node : nodes) {
            if (!node.getNodeId().equals(originNode.getNodeId())) {
                node.enqueueUpdate(update);
            }
        }
    }

    public void synchronize() {
        for (Node node : nodes) {
            executorService.submit(() -> syncNodeWithOthers(node));
        }
    }

    private void syncNodeWithOthers(Node node) {
        for (Node otherNode : nodes) {
            if (!node.getNodeId().equals(otherNode.getNodeId())) {
                node.syncWith(otherNode);
            }
        }
    }

    public void stop() {
        executorService.shutdown();
    }

    public void printNodeStates() {
        for (Node node : nodes) {
            System.out.println("Node " + node.getNodeId() + " synced: " + node.isSynced());
        }
    }

    public static void main(String[] args) throws InterruptedException {
        EventualConsistency consistency = new EventualConsistency(5);

        consistency.updateNode("Node1", "key1", "value1");
        consistency.updateNode("Node2", "key2", "value2");
        consistency.updateNode("Node3", "key1", "newValue1");

        consistency.synchronize();

        Thread.sleep(5000);

        consistency.printNodeStates();
        consistency.stop();
    }
}