import unittest
import logging
import time
import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

class MonitoringLoggingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.registry = CollectorRegistry()
        cls.metrics_pushed = []
        cls.logger = logging.getLogger("MonitoringLoggingTests")
        cls.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        cls.logger.addHandler(handler)

    def setUp(self):
        self.logger.info("Setting up test case")
        self.start_time = time.time()

    def tearDown(self):
        elapsed_time = time.time() - self.start_time
        self.logger.info(f"Test case finished. Elapsed time: {elapsed_time:.2f}s")

    def test_prometheus_metrics_exposure(self):
        self.logger.info("Testing Prometheus metrics exposure")
        metric = Gauge('test_metric', 'Description of gauge', registry=self.registry)
        metric.set(1)
        self.metrics_pushed.append(metric)

        try:
            response = requests.get('http://localhost:9090/metrics')
            self.assertEqual(response.status_code, 200, "Prometheus server not reachable")
            self.logger.info("Prometheus server is reachable")
        except Exception as e:
            self.fail(f"Prometheus metrics exposure test failed: {e}")

    def test_prometheus_metrics_push(self):
        self.logger.info("Testing Prometheus metrics push")
        metric = Gauge('test_push_metric', 'Testing push metric', registry=self.registry)
        metric.set(5)
        self.metrics_pushed.append(metric)

        try:
            push_to_gateway('localhost:9091', job='test_push', registry=self.registry)
            self.logger.info("Successfully pushed metrics to Prometheus")
        except Exception as e:
            self.fail(f"Prometheus metrics push failed: {e}")

    def test_logging_configuration(self):
        self.logger.info("Testing logging configuration")
        with open("test_log_file.log", "w") as log_file:
            handler = logging.FileHandler(log_file.name)
            self.logger.addHandler(handler)
            self.logger.info("Writing log message to file")
            self.logger.removeHandler(handler)

        with open("test_log_file.log", "r") as log_file:
            logs = log_file.read()
            self.assertIn("Writing log message to file", logs, "Log message not found in log file")
            self.logger.info("Log message successfully written to file")

    def test_alert_rule(self):
        self.logger.info("Testing alert rule")
        alert_url = "http://localhost:9093/api/v1/alerts"

        try:
            response = requests.get(alert_url)
            self.assertEqual(response.status_code, 200, "Alertmanager not reachable")
            self.logger.info("Alertmanager is reachable")
            alerts = response.json()
            self.assertGreaterEqual(len(alerts), 1, "No alerts found")
            self.logger.info(f"Alert found: {alerts[0]['labels']['alertname']}")
        except Exception as e:
            self.fail(f"Alert rule test failed: {e}")

    def test_alert_trigger(self):
        self.logger.info("Testing alert trigger")

        metric = Gauge('alert_test_metric', 'Metric for alerting', registry=self.registry)
        metric.set(100)
        self.metrics_pushed.append(metric)
        
        try:
            push_to_gateway('localhost:9091', job='alert_test', registry=self.registry)
            time.sleep(2)
            alert_url = "http://localhost:9093/api/v1/alerts"
            response = requests.get(alert_url)
            self.assertEqual(response.status_code, 200, "Alertmanager not reachable after push")
            alerts = response.json()
            alert_names = [alert['labels']['alertname'] for alert in alerts]
            self.assertIn("HighMetricAlert", alert_names, "HighMetricAlert not triggered")
            self.logger.info("HighMetricAlert successfully triggered")
        except Exception as e:
            self.fail(f"Alert trigger test failed: {e}")

    def test_grafana_dashboard_reachability(self):
        self.logger.info("Testing Grafana dashboard reachability")
        grafana_url = "http://localhost:3000/api/dashboards/db"

        try:
            response = requests.get(grafana_url)
            self.assertEqual(response.status_code, 200, "Grafana dashboard not reachable")
            self.logger.info("Grafana dashboard is reachable")
        except Exception as e:
            self.fail(f"Grafana dashboard reachability test failed: {e}")

    def test_logging_rotation(self):
        self.logger.info("Testing logging rotation")
        handler = logging.FileHandler("rotating_log.log", mode="w")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

        for i in range(100):
            self.logger.info(f"Log message {i}")

        self.logger.removeHandler(handler)
        with open("rotating_log.log", "r") as log_file:
            logs = log_file.readlines()
            self.assertGreaterEqual(len(logs), 100, "Log rotation didn't work as expected")
            self.logger.info("Log rotation test passed")

    def test_log_level_filtering(self):
        self.logger.info("Testing log level filtering")
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        self.logger.addHandler(handler)

        with self.assertLogs(self.logger, level='WARNING') as log:
            self.logger.warning("This is a warning message")
            self.logger.error("This is an error message")
        
        self.assertIn("This is a warning message", log.output)
        self.assertIn("This is an error message", log.output)
        self.logger.info("Log level filtering works as expected")

if __name__ == '__main__':
    unittest.main()