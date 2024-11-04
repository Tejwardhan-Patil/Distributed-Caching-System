import time
import random
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
import json
import logging

# Configuration for load test
CACHE_URL = "http://website.com/api/cache"  # Cache API endpoint
NUM_REQUESTS = 10000  # Total number of requests for the test
NUM_THREADS = 50  # Number of threads to simulate concurrent users
KEY_PREFIX = "load_test_key_"
VALUE_PREFIX = "load_test_value_"
CACHE_HIT_RATIO_THRESHOLD = 0.9  

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Global counters
total_requests = 0
successful_requests = 0
cache_hits = 0
cache_misses = 0
start_time = None
end_time = None

def put_request(key, value):
    """Send a PUT request to cache to store key-value pairs."""
    global total_requests, successful_requests
    try:
        response = requests.put(f"{CACHE_URL}/put", json={"key": key, "value": value})
        if response.status_code == 200:
            successful_requests += 1
        total_requests += 1
    except Exception as e:
        logger.error(f"Failed to perform PUT request: {e}")

def get_request(key):
    """Send a GET request to retrieve values by key."""
    global total_requests, cache_hits, cache_misses
    try:
        response = requests.get(f"{CACHE_URL}/get/{key}")
        if response.status_code == 200:
            if response.json().get("hit", False):
                cache_hits += 1
            else:
                cache_misses += 1
        total_requests += 1
    except Exception as e:
        logger.error(f"Failed to perform GET request: {e}")

def perform_load_test():
    """Main function to simulate load by performing both PUT and GET requests."""
    threads = []
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for i in range(NUM_REQUESTS):
            key = f"{KEY_PREFIX}{random.randint(0, 1000)}"
            value = f"{VALUE_PREFIX}{random.randint(0, 1000)}"
            if random.random() > 0.5:
                executor.submit(put_request, key, value)
            else:
                executor.submit(get_request, key)

def print_summary():
    """Print the summary of the load test results."""
    global total_requests, successful_requests, cache_hits, cache_misses, start_time, end_time
    logger.info("=== Load Test Summary ===")
    logger.info(f"Total Requests: {total_requests}")
    logger.info(f"Successful Requests: {successful_requests}")
    logger.info(f"Cache Hits: {cache_hits}")
    logger.info(f"Cache Misses: {cache_misses}")
    logger.info(f"Cache Hit Ratio: {cache_hits / total_requests:.2f}")
    logger.info(f"Total Time Taken: {end_time - start_time:.2f} seconds")
    logger.info(f"Average Requests Per Second: {total_requests / (end_time - start_time):.2f}")

def main():
    """Main entry point for the load test."""
    global start_time, end_time

    logger.info("Starting load test...")
    start_time = time.time()

    # Run the load test
    perform_load_test()

    end_time = time.time()

    # Print the test summary
    print_summary()

    # Validate the cache hit ratio
    if (cache_hits / total_requests) < CACHE_HIT_RATIO_THRESHOLD:
        logger.warning("Cache hit ratio is below acceptable threshold.")
    else:
        logger.info("Cache hit ratio is within acceptable limits.")

if __name__ == "__main__":
    main()

# Utility functions for extended load testing and metrics collection
def generate_random_key_value_pairs(num_pairs):
    """Generate a list of random key-value pairs."""
    pairs = []
    for _ in range(num_pairs):
        key = f"{KEY_PREFIX}{random.randint(0, 10000)}"
        value = f"{VALUE_PREFIX}{random.randint(0, 10000)}"
        pairs.append((key, value))
    return pairs

def measure_throughput():
    """Measure throughput in requests per second."""
    global start_time, end_time, total_requests
    throughput = total_requests / (end_time - start_time)
    logger.info(f"Throughput: {throughput:.2f} requests/second")
    return throughput

def simulate_traffic(duration_in_seconds):
    """Simulate traffic for a given duration to stress test the cache."""
    global total_requests
    total_requests = 0
    stop_time = time.time() + duration_in_seconds
    while time.time() < stop_time:
        key = f"{KEY_PREFIX}{random.randint(0, 1000)}"
        value = f"{VALUE_PREFIX}{random.randint(0, 1000)}"
        if random.random() > 0.5:
            put_request(key, value)
        else:
            get_request(key)
        total_requests += 1

def latency_test():
    """Measure latency of cache operations."""
    latencies = []
    for _ in range(100):
        key = f"{KEY_PREFIX}{random.randint(0, 1000)}"
        value = f"{VALUE_PREFIX}{random.randint(0, 1000)}"
        start_time = time.time()
        put_request(key, value)
        end_time = time.time()
        latencies.append(end_time - start_time)
    avg_latency = sum(latencies) / len(latencies)
    logger.info(f"Average Latency: {avg_latency:.4f} seconds")

# Stress testing with varying loads
def stress_test():
    """Perform stress test by gradually increasing load."""
    logger.info("Starting stress test...")
    for load in range(1, 11):
        logger.info(f"Simulating load: {load * 1000} requests...")
        perform_load_test()
        logger.info(f"Completed load test for {load * 1000} requests")

def advanced_report():
    """Generate a detailed report of the test results."""
    logger.info("Generating detailed report...")
    throughput = measure_throughput()
    logger.info(f"Throughput: {throughput:.2f} requests per second")
    latency_test()