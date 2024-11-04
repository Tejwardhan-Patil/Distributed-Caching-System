package management.cache_api;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.DELETE;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.Consumes;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import javax.ws.rs.PathParam;
import javax.ws.rs.QueryParam;
import javax.inject.Singleton;

@Singleton
@Path("/cache")
public class Routes {

    private final Map<String, CacheEntry> cache = new HashMap<>();
    private final int CACHE_EXPIRATION_TIME = 10; // Cache expiration time in minutes

    static class CacheEntry {
        String value;
        long timestamp;

        CacheEntry(String value) {
            this.value = value;
            this.timestamp = System.currentTimeMillis();
        }

        boolean isExpired(int expirationTime) {
            long currentTime = System.currentTimeMillis();
            long ageInMinutes = TimeUnit.MILLISECONDS.toMinutes(currentTime - timestamp);
            return ageInMinutes >= expirationTime;
        }
    }

    @GET
    @Path("/get/{key}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getCacheValue(@PathParam("key") String key) {
        if (cache.containsKey(key)) {
            CacheEntry entry = cache.get(key);
            if (entry.isExpired(CACHE_EXPIRATION_TIME)) {
                cache.remove(key);
                return Response.status(Response.Status.NOT_FOUND)
                               .entity("{\"message\":\"Cache entry expired\"}")
                               .build();
            }
            return Response.ok("{\"value\":\"" + entry.value + "\"}")
                           .build();
        } else {
            return Response.status(Response.Status.NOT_FOUND)
                           .entity("{\"message\":\"Key not found in cache\"}")
                           .build();
        }
    }

    @POST
    @Path("/set")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response setCacheValue(@QueryParam("key") String key, String value) {
        if (key == null || key.isEmpty() || value == null || value.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                           .entity("{\"message\":\"Invalid key or value\"}")
                           .build();
        }

        cache.put(key, new CacheEntry(value));
        return Response.ok("{\"message\":\"Cache value set successfully\"}")
                       .build();
    }

    @DELETE
    @Path("/delete/{key}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response deleteCacheValue(@PathParam("key") String key) {
        if (cache.containsKey(key)) {
            cache.remove(key);
            return Response.ok("{\"message\":\"Cache entry deleted\"}")
                           .build();
        } else {
            return Response.status(Response.Status.NOT_FOUND)
                           .entity("{\"message\":\"Key not found in cache\"}")
                           .build();
        }
    }

    @GET
    @Path("/stats")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getCacheStats() {
        int totalEntries = cache.size();
        long totalNonExpired = cache.entrySet()
                                    .stream()
                                    .filter(e -> !e.getValue().isExpired(CACHE_EXPIRATION_TIME))
                                    .count();

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalEntries", totalEntries);
        stats.put("nonExpiredEntries", totalNonExpired);

        return Response.ok(stats).build();
    }

    @DELETE
    @Path("/clear")
    @Produces(MediaType.APPLICATION_JSON)
    public Response clearCache() {
        cache.clear();
        return Response.ok("{\"message\":\"Cache cleared\"}").build();
    }

    private void runCacheCleanupTask() {
        new Thread(() -> {
            while (true) {
                try {
                    TimeUnit.MINUTES.sleep(CACHE_EXPIRATION_TIME);
                    cache.entrySet().removeIf(entry -> entry.getValue().isExpired(CACHE_EXPIRATION_TIME));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }).start();
    }

    public Routes() {
        runCacheCleanupTask();
    }

    @POST
    @Path("/replicate")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response replicateCacheEntry(@QueryParam("key") String key, String value) {
        if (key == null || key.isEmpty() || value == null || value.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                           .entity("{\"message\":\"Invalid key or value\"}")
                           .build();
        }

        cache.put(key, new CacheEntry(value));
        return Response.ok("{\"message\":\"Cache value replicated\"}").build();
    }

    @GET
    @Path("/leader")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getLeaderNode() {
        String leader = "node-1"; 
        return Response.ok("{\"leaderNode\":\"" + leader + "\"}").build();
    }

    @POST
    @Path("/promote")
    @Produces(MediaType.APPLICATION_JSON)
    public Response promoteToLeader(@QueryParam("node") String node) {
        if (node == null || node.isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                           .entity("{\"message\":\"Invalid node\"}")
                           .build();
        }
        return Response.ok("{\"message\":\"Node promoted to leader\"}").build();
    }

    @GET
    @Path("/health")
    @Produces(MediaType.APPLICATION_JSON)
    public Response checkHealth() {
        return Response.ok("{\"status\":\"healthy\"}")
                       .build();
    }

    @GET
    @Path("/nodes")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getActiveNodes() {
        Map<String, String> nodes = new HashMap<>();
        nodes.put("node-1", "active");
        nodes.put("node-2", "active");
        nodes.put("node-3", "active");

        return Response.ok(nodes).build();
    }
}