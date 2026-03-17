# -*- coding: utf-8 -*-
"""
IntentOS Cloud Bootstrap Orchestrator

This module is responsible for the autonomous deployment and management of IntentOS
in a cloud environment. It reads resource definitions, generates an execution
plan, and applies it using the appropriate cloud provider's SDK.
"""

import yaml
import logging
import sys
from typing import Dict, Any, List

from intentos.distributed.cost_monitor import CostMonitor

# Try to import cloud-specific SDKs
try:
    import boto3
    from botocore.exceptions import NoCredentialsError
    AWS_SDK_AVAILABLE = True
except ImportError:
    AWS_SDK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CloudOrchestrator:
    """
    Orchestrates the deployment of cloud infrastructure for IntentOS.
    """

    def __init__(self, provider: str = 'aws', region: str = 'us-east-1'):
        """
        Initializes the orchestrator for a specific cloud provider.

        :param provider: The cloud provider to use (e.g., 'aws', 'gcp', 'azure').
        :param region: The cloud region (e.g., 'us-east-1').
        """
        self.provider = provider
        self.region = region
        self.definitions = None
        self.plan = None
        self.cost_monitor = CostMonitor(provider=self.provider, region=self.region)
        
        logging.info(f"CloudOrchestrator initialized for provider: {self.provider}")
        self._initial_setup()

    def _verify_credentials(self) -> bool:
        """
        Verifies that the necessary cloud credentials are configured.
        """
        logging.info("Verifying cloud credentials...")
        if self.provider == 'aws':
            if not AWS_SDK_AVAILABLE:
                logging.warning("AWS SDK (boto3) not found. Cannot verify credentials.")
                return False
            try:
                # The presence of the STS client doesn't guarantee permissions,
                # but it's a good check for configured credentials.
                boto3.client('sts').get_caller_identity()
                logging.info("AWS credentials found and verified.")
                return True
            except NoCredentialsError:
                logging.warning("AWS credentials not found.")
                return False
        else:
            logging.warning(f"Credential verification for provider '{self.provider}' is not yet implemented.")
            return False

    def _guide_user_for_credentials(self):
        """
        Prints a guide for the user to configure their cloud credentials.
        """
        if self.provider == 'aws':
            guide = """
================================================================================
⚠️  AWS Credentials Not Found
================================================================================

To allow IntentOS to manage cloud resources, you need to configure AWS
credentials. Please follow one of the methods below.

--------------------------------------------------------------------------------
Method 1: Using the AWS CLI (Recommended)
--------------------------------------------------------------------------------
1.  Install the AWS CLI:
    Follow the official guide: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

2.  Configure the CLI:
    Run the following command and enter your Access Key ID and Secret Access Key:

    aws configure

    You will be asked for:
    - AWS Access Key ID: [Your Access Key]
    - AWS Secret Access Key: [Your Secret Key]
    - Default region name: [e.g., us-east-1]
    - Default output format: [json]

--------------------------------------------------------------------------------
Method 2: Using Environment Variables
--------------------------------------------------------------------------------
You can set the credentials as environment variables in your shell:

    export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_ACCESS_KEY"
    export AWS_DEFAULT_REGION="us-east-1"

================================================================================
"""
            print(guide)

    def _initial_setup(self):
        """
        Performs initial setup, including credential verification and user guidance.
        """
        if not self._verify_credentials():
            self._guide_user_for_credentials()
            input("--> Please configure your credentials, then press Enter to continue...")
            if not self._verify_credentials():
                logging.error("Credentials are still not configured. Exiting.")
                sys.exit(1)

    def load_definitions(self, file_path: str) -> None:
        """
        Loads the cloud resource definitions from a YAML file.

        :param file_path: The path to the resource definition YAML file.
        """
        logging.info(f"Loading resource definitions from: {file_path}")
        try:
            with open(file_path, 'r') as f:
                self.definitions = yaml.safe_load(f)
            logging.info("Resource definitions loaded successfully.")
        except FileNotFoundError:
            logging.error(f"Definition file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file: {e}")
            raise

    def generate_plan(self) -> Dict[str, Any]:
        """
        Generates a deployment plan based on the loaded definitions.

        The plan outlines the actions to be taken (create, update, delete)
        for each resource and includes a cost estimate.
        """
        if not self.definitions:
            logging.error("Cannot generate plan: definitions are not loaded.")
            raise ValueError("Resource definitions must be loaded before generating a plan.")

        logging.info("Generating deployment plan...")
        self.plan = {
            'provider': self.provider,
            'actions': []
        }

        # Placeholder logic: For now, assume all defined resources need to be created.
        for resource_name, config in self.definitions.get('resources', {}).items():
            action = {
                'name': resource_name,
                'type': config.get('type'),
                'action': 'create', # Future: could be 'update' or 'delete'
                'details': config.get('properties')
            }
            self.plan['actions'].append(action)

        # Add cost estimate to the plan
        cost_estimate = self.cost_monitor.get_plan_cost_estimate(self.plan)
        self.plan['estimated_cost'] = cost_estimate

        logging.info("Deployment plan generated successfully.")
        print("\n" + "="*80)
        print("DEPLOYMENT PLAN SUMMARY")
        print("="*80)
        for action in self.plan['actions']:
            print(f"- Action: {action['action']:<10} | Resource: {action['name']:<25} | Type: {action['type']}")
        print("-"*80)
        print(f"💰 Estimated Total Monthly Cost: ${self.plan['estimated_cost']['total_monthly_cost']}")
        print("="*80 + "\n")
        
        return self.plan

    def execute_plan(self, auto_approve: bool = False) -> None:
        """
        Executes the generated deployment plan.

        This method makes the actual changes to the cloud infrastructure.
        It asks for user confirmation unless auto_approve is True.
        """
        if not self.plan:
            logging.error("Cannot execute plan: no plan has been generated.")
            raise ValueError("A plan must be generated before it can be executed.")

        if not auto_approve:
            estimated_cost = self.plan['estimated_cost']['total_monthly_cost']
            print(f"You are about to apply a plan that is estimated to cost ${estimated_cost}/month.")
            confirm = input("--> Do you want to proceed? (yes/no): ")
            if confirm.lower() != 'yes':
                logging.warning("Execution cancelled by user.")
                return

        logging.info("Executing deployment plan...")

        # Placeholder logic: Loop through actions and "pretend" to create them.
        for action in self.plan.get('actions', []):
            if action['action'] == 'create':
                logging.info(f"  [CREATE] Resource '{action['name']}' of type '{action['type']}' with details: {action['details']}")
            else:
                logging.warning(f"Action '{action['action']}' is not yet implemented.")

        logging.info("Deployment plan executed successfully.")

if __name__ == '__main__':
    # This is a simple demonstration of how the orchestrator will be used.
    # It requires a 'resources.yml' file for the demonstration.
    
    # Create a dummy resource definition file for testing
    dummy_resources = {
        "provider": "aws",
        "region": "us-east-1",
        "resources": {
            "intentos_vpc": {
                "type": "vpc",
                "properties": {
                    "cidr_block": "10.0.0.0/16",
                    "tags": {"Name": "intentos-vpc"}
                }
            },
            "intentos_cluster": {
                "type": "ecs_cluster",
                "properties": {
                    "cluster_name": "intentos-main-cluster"
                }
            },
            "intentos_node_group": {
                "type": "ec2_instance",
                "properties": {
                    "instance_type": "t3.micro"
                }
            }
        }
    }
    # Create dummy directory if it does not exist
    import os
    if not os.path.exists("cloud/aws"):
        os.makedirs("cloud/aws")

    with open("cloud/aws/resources.yml", "w") as f:
        yaml.dump(dummy_resources, f)

    orchestrator = CloudOrchestrator(provider='aws', region='us-east-1')
    orchestrator.load_definitions('cloud/aws/resources.yml')
    plan = orchestrator.generate_plan()
    orchestrator.execute_plan()
