package distributed.partitioning;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.SortedMap;
import java.util.TreeMap;
import java.util.ArrayList;
import java.util.List;
import java.util.Collection;
import java.util.Collections;

public class ConsistentHashing<T> {

    private final HashFunction hashFunction;
    private final int numberOfReplicas;
    private final SortedMap<Integer, T> circle = new TreeMap<>();

    public ConsistentHashing(HashFunction hashFunction, int numberOfReplicas, Collection<T> nodes) {
        this.hashFunction = hashFunction;
        this.numberOfReplicas = numberOfReplicas;

        for (T node : nodes) {
            add(node);
        }
    }

    // Adds a node into the consistent hashing circle
    public void add(T node) {
        for (int i = 0; i < numberOfReplicas; i++) {
            circle.put(hashFunction.hash(node.toString() + i), node);
        }
    }

    // Removes a node from the consistent hashing circle
    public void remove(T node) {
        for (int i = 0; i < numberOfReplicas; i++) {
            circle.remove(hashFunction.hash(node.toString() + i));
        }
    }

    // Maps a key to a node in the consistent hashing circle
    public T getNodeForKey(String key) {
        if (circle.isEmpty()) {
            return null;
        }
        int hash = hashFunction.hash(key);
        if (!circle.containsKey(hash)) {
            SortedMap<Integer, T> tailMap = circle.tailMap(hash);
            hash = tailMap.isEmpty() ? circle.firstKey() : tailMap.firstKey();
        }
        return circle.get(hash);
    }

    public static class HashFunction {
        private static final String HASH_ALGORITHM = "SHA-256";

        public int hash(Object key) {
            try {
                MessageDigest md = MessageDigest.getInstance(HASH_ALGORITHM);
                byte[] digest = md.digest(key.toString().getBytes(StandardCharsets.UTF_8));
                return Math.abs(new String(digest).hashCode());
            } catch (NoSuchAlgorithmException e) {
                throw new RuntimeException("No such algorithm: " + HASH_ALGORITHM, e);
            }
        }
    }

    public static void main(String[] args) {
        List<String> nodes = new ArrayList<>();
        nodes.add("NodeA");
        nodes.add("NodeB");
        nodes.add("NodeC");

        ConsistentHashing<String> consistentHashing = new ConsistentHashing<>(new HashFunction(), 3, nodes);

        String[] keys = {"Key1", "Key2", "Key3", "Key4", "Key5"};

        for (String key : keys) {
            System.out.println("Key: " + key + " is mapped to Node: " + consistentHashing.getNodeForKey(key));
        }

        System.out.println("\nAdding NodeD");
        consistentHashing.add("NodeD");

        for (String key : keys) {
            System.out.println("Key: " + key + " is now mapped to Node: " + consistentHashing.getNodeForKey(key));
        }

        System.out.println("\nRemoving NodeB");
        consistentHashing.remove("NodeB");

        for (String key : keys) {
            System.out.println("Key: " + key + " is now mapped to Node: " + consistentHashing.getNodeForKey(key));
        }
    }
}