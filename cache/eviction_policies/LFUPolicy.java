package cache.eviction_policies;

import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;

public class LFUPolicy<K, V> {

    private final int capacity;
    private Map<K, V> cache;
    private Map<K, Integer> frequencyMap;
    private Map<Integer, LinkedHashSet<K>> frequencyListMap;
    private int minFrequency;

    public LFUPolicy(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        this.frequencyMap = new HashMap<>();
        this.frequencyListMap = new HashMap<>();
        this.minFrequency = 0;
    }

    public V get(K key) {
        if (!cache.containsKey(key)) {
            return null;
        }
        // Update the frequency
        int frequency = frequencyMap.get(key);
        frequencyMap.put(key, frequency + 1);

        // Remove the key from the current frequency list
        frequencyListMap.get(frequency).remove(key);

        // If the frequency list is empty and it's the minFrequency, update minFrequency
        if (frequencyListMap.get(frequency).isEmpty()) {
            frequencyListMap.remove(frequency);
            if (frequency == minFrequency) {
                minFrequency++;
            }
        }

        // Add the key to the new frequency list
        frequencyListMap.computeIfAbsent(frequency + 1, k -> new LinkedHashSet<>()).add(key);

        return cache.get(key);
    }

    public void put(K key, V value) {
        if (capacity <= 0) {
            return;
        }

        // If the key already exists, update the value and increase the frequency
        if (cache.containsKey(key)) {
            cache.put(key, value);
            get(key); // Update the frequency using the get method
            return;
        }

        // If the cache is full, remove the least frequently used element
        if (cache.size() >= capacity) {
            evict();
        }

        // Insert the new key-value pair
        cache.put(key, value);
        frequencyMap.put(key, 1);
        frequencyListMap.computeIfAbsent(1, k -> new LinkedHashSet<>()).add(key);
        minFrequency = 1;
    }

    private void evict() {
        // Get the least frequently used key from the minFrequency list
        LinkedHashSet<K> keys = frequencyListMap.get(minFrequency);
        K keyToRemove = keys.iterator().next();
        keys.remove(keyToRemove);

        // If the list becomes empty, remove it from the frequency list map
        if (keys.isEmpty()) {
            frequencyListMap.remove(minFrequency);
        }

        // Remove the key from the cache and the frequency map
        cache.remove(keyToRemove);
        frequencyMap.remove(keyToRemove);
    }

    public void display() {
        System.out.println("Cache Contents: " + cache.toString());
        System.out.println("Frequency Map: " + frequencyMap.toString());
        System.out.println("Frequency List Map: " + frequencyListMap.toString());
    }

    public static void main(String[] args) {
        LFUPolicy<Integer, String> lfuCache = new LFUPolicy<>(3);

        lfuCache.put(1, "A");
        lfuCache.put(2, "B");
        lfuCache.put(3, "C");
        lfuCache.display();

        lfuCache.get(1);
        lfuCache.put(4, "D");
        lfuCache.display();

        lfuCache.get(3);
        lfuCache.get(3);
        lfuCache.put(5, "E");
        lfuCache.display();
    }
}