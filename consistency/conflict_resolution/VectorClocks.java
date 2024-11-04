package consistency.conflict_resolution;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

/**
 * VectorClocks class handles conflict resolution using vector clocks
 * in distributed systems.
 */
public class VectorClocks implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    private Map<String, Integer> clock; // Vector clock
    
    public VectorClocks() {
        this.clock = new HashMap<>();
    }

    /**
     * Updates the vector clock for a specific node.
     *
     * @param nodeId The ID of the node.
     */
    public void increment(String nodeId) {
        this.clock.put(nodeId, this.clock.getOrDefault(nodeId, 0) + 1);
    }

    /**
     * Merges the current vector clock with another vector clock.
     * 
     * @param otherClock The other vector clock to be merged.
     */
    public void merge(VectorClocks otherClock) {
        for (Map.Entry<String, Integer> entry : otherClock.clock.entrySet()) {
            String nodeId = entry.getKey();
            int otherValue = entry.getValue();
            int currentValue = this.clock.getOrDefault(nodeId, 0);
            this.clock.put(nodeId, Math.max(currentValue, otherValue));
        }
    }

    /**
     * Compares the current vector clock with another vector clock.
     * 
     * @param otherClock The other vector clock to compare with.
     * @return Returns 1 if this clock is greater, -1 if less, 0 if concurrent.
     */
    public int compare(VectorClocks otherClock) {
        boolean thisBigger = false;
        boolean otherBigger = false;

        Set<String> allNodes = new HashSet<>(this.clock.keySet());
        allNodes.addAll(otherClock.clock.keySet());

        for (String nodeId : allNodes) {
            int thisValue = this.clock.getOrDefault(nodeId, 0);
            int otherValue = otherClock.clock.getOrDefault(nodeId, 0);

            if (thisValue > otherValue) {
                thisBigger = true;
            } else if (thisValue < otherValue) {
                otherBigger = true;
            }

            if (thisBigger && otherBigger) {
                return 0; // Concurrent
            }
        }

        if (thisBigger) {
            return 1;
        } else if (otherBigger) {
            return -1;
        }
        return 0; // Equal
    }

    /**
     * Checks if the current vector clock happens-before another vector clock.
     * 
     * @param otherClock The other vector clock.
     * @return Returns true if this clock happens-before otherClock.
     */
    public boolean happensBefore(VectorClocks otherClock) {
        boolean atLeastOneSmaller = false;

        for (Map.Entry<String, Integer> entry : this.clock.entrySet()) {
            String nodeId = entry.getKey();
            int thisValue = entry.getValue();
            int otherValue = otherClock.clock.getOrDefault(nodeId, 0);

            if (thisValue > otherValue) {
                return false;
            }

            if (thisValue < otherValue) {
                atLeastOneSmaller = true;
            }
        }

        return atLeastOneSmaller;
    }

    /**
     * Resets the vector clock for a specific node.
     *
     * @param nodeId The ID of the node.
     */
    public void reset(String nodeId) {
        this.clock.put(nodeId, 0);
    }

    /**
     * Returns the current state of the vector clock.
     * 
     * @return A string representing the vector clock.
     */
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("{");
        for (Map.Entry<String, Integer> entry : this.clock.entrySet()) {
            sb.append(entry.getKey()).append(": ").append(entry.getValue()).append(", ");
        }
        if (sb.length() > 1) {
            sb.setLength(sb.length() - 2); // Remove last comma
        }
        sb.append("}");
        return sb.toString();
    }

    /**
     * Resolves conflicts between two versions of data using vector clocks.
     * 
     * @param currentClock Current vector clock.
     * @param newClock New vector clock.
     * @return Returns the clock of the latest update.
     */
    public static VectorClocks resolve(VectorClocks currentClock, VectorClocks newClock) {
        int comparison = currentClock.compare(newClock);

        if (comparison > 0) {
            return currentClock; // Current clock is more recent
        } else if (comparison < 0) {
            return newClock; // New clock is more recent
        }

        // Conflict: merge clocks and handle accordingly
        VectorClocks mergedClock = new VectorClocks();
        mergedClock.merge(currentClock);
        mergedClock.merge(newClock);
        return mergedClock;
    }

    /**
     * Serializes the vector clock for storage or transmission.
     * 
     * @return A byte array representing the serialized clock.
     */
    public byte[] serialize() {
        try {
            java.io.ByteArrayOutputStream baos = new java.io.ByteArrayOutputStream();
            java.io.ObjectOutputStream oos = new java.io.ObjectOutputStream(baos);
            oos.writeObject(this);
            oos.flush();
            return baos.toByteArray();
        } catch (java.io.IOException e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * Deserializes a byte array back into a vector clock.
     * 
     * @param bytes The byte array representing the serialized clock.
     * @return A VectorClocks object.
     */
    public static VectorClocks deserialize(byte[] bytes) {
        try {
            java.io.ByteArrayInputStream bais = new java.io.ByteArrayInputStream(bytes);
            java.io.ObjectInputStream ois = new java.io.ObjectInputStream(bais);
            return (VectorClocks) ois.readObject();
        } catch (java.io.IOException | ClassNotFoundException e) {
            e.printStackTrace();
            return null;
        }
    }

    /**
     * Checks equality between two vector clocks.
     * 
     * @param otherClock The other vector clock.
     * @return True if both clocks are equal.
     */
    @Override
    public boolean equals(Object otherClock) {
        if (this == otherClock) {
            return true;
        }
        if (otherClock == null || getClass() != otherClock.getClass()) {
            return false;
        }
        VectorClocks that = (VectorClocks) otherClock;
        return this.clock.equals(that.clock);
    }

    @Override
    public int hashCode() {
        return this.clock.hashCode();
    }

    /**
     * Retrieves the value of a node's clock.
     * 
     * @param nodeId The ID of the node.
     * @return The clock value for the node.
     */
    public int getClockValue(String nodeId) {
        return this.clock.getOrDefault(nodeId, 0);
    }
}