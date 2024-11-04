package cache.serialization;

import com.google.protobuf.InvalidProtocolBufferException;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import cache.model.CacheObjectProto.CacheObject;

/**
 * ProtobufSerializer is responsible for serializing and deserializing cache data 
 * using Protocol Buffers for efficient transfer and storage.
 */
public class ProtobufSerializer {

    /**
     * Serializes the given CacheObject into a byte array.
     * 
     * @param cacheObject the cache object to serialize
     * @return a byte array representing the serialized cache object
     * @throws IOException if an error occurs during serialization
     */
    public byte[] serialize(CacheObject cacheObject) throws IOException {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        try {
            cacheObject.writeTo(byteArrayOutputStream);
        } finally {
            byteArrayOutputStream.close();
        }
        return byteArrayOutputStream.toByteArray();
    }

    /**
     * Deserializes a byte array into a CacheObject.
     * 
     * @param data the byte array containing serialized cache object data
     * @return the deserialized CacheObject
     * @throws InvalidProtocolBufferException if deserialization fails
     */
    public CacheObject deserialize(byte[] data) throws InvalidProtocolBufferException {
        return CacheObject.parseFrom(data);
    }

    /**
     * Serializes the given CacheObject to an OutputStream.
     * 
     * @param cacheObject the cache object to serialize
     * @param outputStream the output stream to write serialized data to
     * @throws IOException if an error occurs during serialization
     */
    public void serializeToStream(CacheObject cacheObject, OutputStream outputStream) throws IOException {
        try {
            cacheObject.writeTo(outputStream);
        } finally {
            outputStream.close();
        }
    }

    /**
     * Deserializes data from an InputStream into a CacheObject.
     * 
     * @param inputStream the input stream containing serialized cache object data
     * @return the deserialized CacheObject
     * @throws IOException if deserialization fails
     */
    public CacheObject deserializeFromStream(InputStream inputStream) throws IOException {
        byte[] data = toByteArray(inputStream);
        return CacheObject.parseFrom(data);
    }

    /**
     * A utility method to convert InputStream data into a byte array.
     * 
     * @param inputStream the input stream to read from
     * @return a byte array containing the stream's data
     * @throws IOException if an error occurs while reading the stream
     */
    private byte[] toByteArray(InputStream inputStream) throws IOException {
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        byte[] buffer = new byte[1024];
        int length;
        while ((length = inputStream.read(buffer)) != -1) {
            byteArrayOutputStream.write(buffer, 0, length);
        }
        return byteArrayOutputStream.toByteArray();
    }

    /**
     * Converts a CacheObject into a human-readable JSON string.
     * 
     * @param cacheObject the cache object to convert
     * @return a JSON string representing the cache object
     */
    public String toJson(CacheObject cacheObject) {
        return cacheObject.toString(); // CacheObject's toString() provides JSON-like structure
    }

    /**
     * CacheObject usage.
     * This method demonstrates how to create, serialize, and deserialize a CacheObject.
     */
    public static void main(String[] args) {
        ProtobufSerializer serializer = new ProtobufSerializer();

        // Create a sample CacheObject
        CacheObject cacheObject = CacheObject.newBuilder()
                .setId(1)
                .setKey("testKey")
                .setValue("testValue")
                .setExpirationTime(System.currentTimeMillis() + 60000)
                .build();

        try {
            // Serialize CacheObject to byte array
            byte[] serializedData = serializer.serialize(cacheObject);
            System.out.println("Serialized Data: " + new String(serializedData));

            // Deserialize CacheObject from byte array
            CacheObject deserializedObject = serializer.deserialize(serializedData);
            System.out.println("Deserialized Object: " + deserializedObject);

            // Convert to JSON
            String json = serializer.toJson(deserializedObject);
            System.out.println("JSON Representation: " + json);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}