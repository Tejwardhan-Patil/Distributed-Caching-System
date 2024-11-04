import unittest
import subprocess
import requests
import yaml
import os
import time

class DeploymentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Prepare the environment by loading configurations and initializing variables."""
        cls.load_configuration()
        cls.kubernetes_config_file = "deployment/kubernetes/K8sManifests.yaml"
        cls.docker_compose_file = "deployment/docker/DockerCompose.yml"
        cls.cloudformation_file = "deployment/cloudformation/CFTemplate.yaml"

    @classmethod
    def load_configuration(cls):
        """Load the deployment configuration file."""
        config_file = os.getenv('DEPLOYMENT_CONFIG', 'configs/config.dev.yaml')
        with open(config_file, 'r') as stream:
            cls.config = yaml.safe_load(stream)

    def test_docker_compose(self):
        """Test the Docker Compose deployment by starting the services."""
        self.run_command(f"docker-compose -f {self.docker_compose_file} up -d")
        time.sleep(10)  # Give containers time to initialize
        self.verify_service_health("http://localhost:5000/health")

    def test_kubernetes_deployment(self):
        """Test Kubernetes deployment by applying manifests."""
        self.run_command(f"kubectl apply -f {self.kubernetes_config_file}")
        time.sleep(15)  # Allow time for pods to be created
        self.verify_pods_running()
        self.verify_service_health(self.config['kubernetes_service_url'])

    def test_cloudformation_stack(self):
        """Test AWS CloudFormation deployment by creating a stack."""
        stack_name = self.config['cloudformation_stack_name']
        self.run_command(f"aws cloudformation create-stack --stack-name {stack_name} --template-body file://{self.cloudformation_file}")
        self.wait_for_stack_completion(stack_name)
        self.verify_service_health(self.config['cloudformation_service_url'])

    def test_terraform_provisioning(self):
        """Test Terraform provisioning for cloud resources."""
        terraform_dir = "deployment/terraform"
        self.run_command(f"terraform -chdir={terraform_dir} init")
        self.run_command(f"terraform -chdir={terraform_dir} apply -auto-approve")
        self.verify_service_health(self.config['terraform_service_url'])

    def test_rollback_on_failure(self):
        """Test rollback functionality if deployment fails."""
        try:
            self.run_command(f"kubectl apply -f {self.kubernetes_config_file} --dry-run=client")
            raise Exception("Intentional failure for rollback test")
        except Exception:
            self.run_command(f"kubectl delete -f {self.kubernetes_config_file}")
            print("Rollback successful")

    def test_post_deployment_functionality(self):
        """Test if the cache system works after deployment."""
        cache_url = f"{self.config['cache_service_url']}/cache"
        payload = {"key": "test_key", "value": "test_value"}
        response = requests.post(cache_url, json=payload)
        self.assertEqual(response.status_code, 200, "Failed to insert value into cache")

        response = requests.get(f"{cache_url}/test_key")
        self.assertEqual(response.status_code, 200, "Failed to retrieve value from cache")
        self.assertEqual(response.json().get('value'), "test_value", "Cache value mismatch")

    def test_failover(self):
        """Test failover scenario by shutting down primary node and ensuring failover."""
        primary_node = self.config['primary_node']
        secondary_node = self.config['secondary_node']

        self.run_command(f"kubectl drain {primary_node} --ignore-daemonsets")
        time.sleep(10)
        self.verify_service_health(f"http://{secondary_node}/health")
        self.run_command(f"kubectl uncordon {primary_node}")

    def test_monitoring_setup(self):
        """Test if monitoring is set up and metrics are exposed."""
        metrics_url = f"{self.config['monitoring_service_url']}/metrics"
        response = requests.get(metrics_url)
        self.assertEqual(response.status_code, 200, "Metrics service is not available")
        self.assertIn("cache_hits_total", response.text, "Cache hit metrics not found")

    def test_alerting_rules(self):
        """Test if alerting rules are properly configured and triggered."""
        alerts_url = f"{self.config['alerting_service_url']}/alerts"
        response = requests.get(alerts_url)
        self.assertEqual(response.status_code, 200, "Alerts service is not available")
        self.assertIn("firing", response.text, "No active alerts found")

    @staticmethod
    def run_command(command):
        """Run a shell command and raise an exception if it fails."""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Command failed: {command}\n{stderr.decode('utf-8')}")

    def verify_service_health(self, health_url):
        """Verify if the service is healthy by checking the health endpoint."""
        response = requests.get(health_url)
        self.assertEqual(response.status_code, 200, f"Health check failed for {health_url}")

    def verify_pods_running(self):
        """Verify that all Kubernetes pods are running."""
        output = subprocess.check_output("kubectl get pods", shell=True)
        pod_statuses = output.decode('utf-8').split('\n')
        for status in pod_statuses:
            if 'Running' not in status:
                raise Exception(f"Pod is not running: {status}")

    def wait_for_stack_completion(self, stack_name):
        """Wait for AWS CloudFormation stack creation to complete."""
        status = ""
        while status != "CREATE_COMPLETE":
            output = subprocess.check_output(f"aws cloudformation describe-stacks --stack-name {stack_name}", shell=True)
            stack_info = yaml.safe_load(output)
            status = stack_info['Stacks'][0]['StackStatus']
            if status == "CREATE_FAILED":
                raise Exception(f"CloudFormation stack creation failed: {stack_name}")
            time.sleep(5)

if __name__ == '__main__':
    unittest.main()