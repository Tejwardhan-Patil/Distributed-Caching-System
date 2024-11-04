#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: ./CacheBenchmark.sh [OPTIONS]"
    echo "Options:"
    echo "  -c <config_file>       Path to the configuration file (YAML)"
    echo "  -n <num_requests>      Number of requests to simulate"
    echo "  -t <threads>           Number of threads to use"
    echo "  -h                     Show this help message"
}

# Parse command-line arguments
while getopts ":c:n:t:h" opt; do
  case ${opt} in
    c )
      CONFIG_FILE=$OPTARG
      ;;
    n )
      NUM_REQUESTS=$OPTARG
      ;;
    t )
      THREADS=$OPTARG
      ;;
    h )
      usage
      exit 0
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      usage
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      usage
      exit 1
      ;;
  esac
done

# Ensure required arguments are provided
if [ -z "${CONFIG_FILE}" ] || [ -z "${NUM_REQUESTS}" ] || [ -z "${THREADS}" ]; then
    echo "Missing required arguments."
    usage
    exit 1
fi

# Load configuration
echo "Loading configuration from ${CONFIG_FILE}..."
source ${CONFIG_FILE}

# Start Monitoring Services
echo "Starting Prometheus for metrics collection..."
docker-compose -f docker/Prometheus.yml up -d

echo "Starting Grafana for monitoring dashboard..."
docker-compose -f docker/Grafana.yml up -d

# Run Load Test
echo "Running load test with ${NUM_REQUESTS} requests and ${THREADS} threads..."
python3 tests/performance_tests/LoadTest.py --config ${CONFIG_FILE} --requests ${NUM_REQUESTS} --threads ${THREADS}

# Collect Metrics
echo "Collecting metrics..."
PROMETHEUS_EXPORTER="monitoring/metrics/PrometheusExporter.py"
python3 $PROMETHEUS_EXPORTER --config ${CONFIG_FILE}

# Display Dashboard URL
GRAFANA_URL="http://localhost:3000"
echo "Benchmark complete. View Grafana dashboard at ${GRAFANA_URL}"

# Stop Monitoring Services
echo "Stopping Prometheus and Grafana services..."
docker-compose -f docker/Prometheus.yml down
docker-compose -f docker/Grafana.yml down

echo "Cache benchmark completed successfully!"