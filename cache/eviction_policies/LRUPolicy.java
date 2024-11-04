package cache.eviction_policies;

import java.util.HashMap;
import java.util.Map;

/**
 * This class implements the Least Recently Used (LRU) eviction policy.
 * It maintains a doubly linked list to track the usage order of cache elements
 * and a hash map for O(1) access to the cache elements.
 */
public class LRUPolicy<K, V> {

    private final int capacity;
    private final Map<K, Node<K, V>> cache;
    private final DoublyLinkedList<K, V> usageList;

    public LRUPolicy(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        this.usageList = new DoublyLinkedList<>();
    }

    /**
     * Get the value associated with the key from the cache.
     * If the key is present, it's marked as recently used.
     *
     * @param key the key to look up in the cache
     * @return the value associated with the key, or null if not present
     */
    public V get(K key) {
        if (!cache.containsKey(key)) {
            return null;
        }

        // Move the accessed node to the head of the list (most recently used)
        Node<K, V> node = cache.get(key);
        usageList.moveToHead(node);
        return node.value;
    }

    /**
     * Put a new key-value pair into the cache. If the cache is full, evict the least recently used entry.
     *
     * @param key   the key to insert/update in the cache
     * @param value the value to associate with the key
     */
    public void put(K key, V value) {
        if (cache.containsKey(key)) {
            // Update existing key and move it to the head of the usage list
            Node<K, V> node = cache.get(key);
            node.value = value;
            usageList.moveToHead(node);
        } else {
            // Add a new key-value pair to the cache
            if (cache.size() >= capacity) {
                // Evict the least recently used item
                Node<K, V> tail = usageList.removeTail();
                if (tail != null) {
                    cache.remove(tail.key);
                }
            }
            Node<K, V> newNode = new Node<>(key, value);
            usageList.addToHead(newNode);
            cache.put(key, newNode);
        }
    }

    /**
     * Remove a key from the cache.
     *
     * @param key the key to remove
     */
    public void remove(K key) {
        if (cache.containsKey(key)) {
            Node<K, V> node = cache.get(key);
            usageList.removeNode(node);
            cache.remove(key);
        }
    }

    /**
     * Get the current size of the cache.
     *
     * @return the size of the cache
     */
    public int size() {
        return cache.size();
    }

    /**
     * Clear the cache and usage list.
     */
    public void clear() {
        cache.clear();
        usageList.clear();
    }

    /**
     * A doubly linked list that keeps track of the usage order of cache elements.
     */
    private static class DoublyLinkedList<K, V> {
        private Node<K, V> head;
        private Node<K, V> tail;

        public DoublyLinkedList() {
            head = null;
            tail = null;
        }

        /**
         * Add a node to the head of the list.
         *
         * @param node the node to add
         */
        public void addToHead(Node<K, V> node) {
            if (head == null) {
                head = tail = node;
            } else {
                node.next = head;
                head.prev = node;
                head = node;
            }
        }

        /**
         * Move a node to the head of the list.
         *
         * @param node the node to move
         */
        public void moveToHead(Node<K, V> node) {
            if (node == head) {
                return; // Already at head
            }

            if (node == tail) {
                tail = tail.prev;
                if (tail != null) {
                    tail.next = null;
                }
            } else {
                node.prev.next = node.next;
                node.next.prev = node.prev;
            }

            node.prev = null;
            node.next = head;
            head.prev = node;
            head = node;
        }

        /**
         * Remove the tail node (least recently used element).
         *
         * @return the removed node
         */
        public Node<K, V> removeTail() {
            if (tail == null) {
                return null;
            }

            Node<K, V> oldTail = tail;
            if (tail.prev != null) {
                tail.prev.next = null;
                tail = tail.prev;
            } else {
                head = tail = null; // The list is now empty
            }
            oldTail.prev = null; // Disconnect the old tail node
            return oldTail;
        }

        /**
         * Remove a specific node from the list.
         *
         * @param node the node to remove
         */
        public void removeNode(Node<K, V> node) {
            if (node == head && node == tail) {
                head = tail = null;
            } else if (node == head) {
                head = head.next;
                head.prev = null;
            } else if (node == tail) {
                tail = tail.prev;
                tail.next = null;
            } else {
                node.prev.next = node.next;
                node.next.prev = node.prev;
            }

            node.prev = null;
            node.next = null;
        }

        /**
         * Clear the entire list.
         */
        public void clear() {
            head = null;
            tail = null;
        }
    }

    /**
     * Node class for the doubly linked list.
     */
    private static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;

        public Node(K key, V value) {
            this.key = key;
            this.value = value;
            this.prev = null;
            this.next = null;
        }
    }
}