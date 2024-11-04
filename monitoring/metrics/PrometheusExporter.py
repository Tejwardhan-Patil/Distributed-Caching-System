from prometheus_client import start_http_server, Summary, Counter, Gauge, Histogram
import random
import time
import threading

# Metrics Definitions
CACHE_HIT_COUNTER = Counter('cache_hits_total', 'Total number of cache hits')
CACHE_MISS_COUNTER = Counter('cache_misses_total', 'Total number of cache misses')
CACHE_SIZE_GAUGE = Gauge('cache_size_bytes', 'Current size of the cache in bytes')
CACHE_ITEMS_GAUGE = Gauge('cache_items_total', 'Current number of items in the cache')
CACHE_LATENCY_HISTOGRAM = Histogram('cache_request_latency_seconds', 'Cache request latency in seconds')
CACHE_WRITE_TIME = Summary('cache_write_duration_seconds', 'Time spent writing to cache')

# Network request metrics
REQUEST_COUNT = Counter('request_count_total', 'Total number of cache requests')
REQUEST_ERRORS = Counter('request_errors_total', 'Total number of cache request errors')

# Cache eviction policies metrics
LRU_EVICTION_COUNTER = Counter('lru_evictions_total', 'Total number of LRU evictions')
LFU_EVICTION_COUNTER = Counter('lfu_evictions_total', 'Total number of LFU evictions')
FIFO_EVICTION_COUNTER = Counter('fifo_evictions_total', 'Total number of FIFO evictions')

# Disk persistence metrics
DISK_WRITE_COUNTER = Counter('disk_write_total', 'Total number of writes to disk')
DISK_READ_COUNTER = Counter('disk_read_total', 'Total number of reads from disk')
DISK_LATENCY_HISTOGRAM = Histogram('disk_request_latency_seconds', 'Disk request latency in seconds')

# Replication metrics
REPLICATION_FAILURES_COUNTER = Counter('replication_failures_total', 'Total number of replication failures')
REPLICATION_LATENCY = Histogram('replication_latency_seconds', 'Replication latency in seconds')

# Snapshot metrics
SNAPSHOT_COUNTER = Counter('snapshot_total', 'Total number of snapshots taken')
SNAPSHOT_LATENCY_HISTOGRAM = Histogram('snapshot_latency_seconds', 'Snapshot latency in seconds')

# Conflict resolution in multi-master replication
MULTI_MASTER_CONFLICTS_COUNTER = Counter('multi_master_conflicts_total', 'Total number of multi-master conflicts')
CONFLICT_RESOLUTION_LATENCY = Summary('conflict_resolution_duration_seconds', 'Time spent resolving conflicts')

def cache_hit():
    CACHE_HIT_COUNTER.inc()

def cache_miss():
    CACHE_MISS_COUNTER.inc()

def cache_write():
    with CACHE_WRITE_TIME.time():
        time.sleep(random.uniform(0.001, 0.1))  # Simulate random write duration

def cache_eviction(eviction_policy):
    if eviction_policy == 'LRU':
        LRU_EVICTION_COUNTER.inc()
    elif eviction_policy == 'LFU':
        LFU_EVICTION_COUNTER.inc()
    elif eviction_policy == 'FIFO':
        FIFO_EVICTION_COUNTER.inc()

def disk_write():
    DISK_WRITE_COUNTER.inc()
    with DISK_LATENCY_HISTOGRAM.time():
        time.sleep(random.uniform(0.001, 0.05))  # Simulate random disk write latency

def disk_read():
    DISK_READ_COUNTER.inc()
    with DISK_LATENCY_HISTOGRAM.time():
        time.sleep(random.uniform(0.001, 0.05))  # Simulate random disk read latency

def replication():
    if random.random() > 0.95:
        REPLICATION_FAILURES_COUNTER.inc()  # Simulate a replication failure
    else:
        with REPLICATION_LATENCY.time():
            time.sleep(random.uniform(0.01, 0.1))  # Simulate random replication latency

def snapshot():
    SNAPSHOT_COUNTER.inc()
    with SNAPSHOT_LATENCY_HISTOGRAM.time():
        time.sleep(random.uniform(0.1, 0.5))  # Simulate snapshot latency

def conflict_resolution():
    MULTI_MASTER_CONFLICTS_COUNTER.inc()
    with CONFLICT_RESOLUTION_LATENCY.time():
        time.sleep(random.uniform(0.01, 0.2))  # Simulate conflict resolution latency

def update_cache_metrics():
    CACHE_SIZE_GAUGE.set(random.uniform(10**6, 10**8))  # Cache size between 1MB and 100MB
    CACHE_ITEMS_GAUGE.set(random.randint(10**3, 10**6))  # Cache items between 1,000 and 1,000,000

def process_request():
    REQUEST_COUNT.inc()
    request_time = random.uniform(0.01, 1.0)
    with CACHE_LATENCY_HISTOGRAM.time():
        time.sleep(request_time)
    if random.random() > 0.8:
        REQUEST_ERRORS.inc()

def run_metrics_server():
    start_http_server(8000) 
    while True:
        # Simulate cache operations
        update_cache_metrics()
        cache_hit()
        cache_miss()
        cache_write()
        cache_eviction(random.choice(['LRU', 'LFU', 'FIFO']))
        disk_write()
        disk_read()
        replication()
        snapshot()
        conflict_resolution()
        process_request()
        time.sleep(5)  # Collect metrics every 5 seconds

if __name__ == '__main__':
    print("Starting Prometheus metrics exporter on port 8000")
    start_simulation_thread = threading.Thread(target=run_metrics_server)
    start_simulation_thread.start()