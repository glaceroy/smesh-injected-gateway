"""
Filename      : revert_back_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will revert the resource quota memory and CPU to their original values from the backup taken earlier for the smesh namespaces.
"""

import logging
import os
import subprocess
import sys
import types
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import requests

import kubernetes.client.rest
import yaml
from kubernetes import client


def log_newline(self, how_many_lines=1):

    # Switch formatter, output a blank line
    self.handler.setFormatter(self.blank_formatter)

    for i in range(how_many_lines):
        self.info("")

    # Switch back
    self.handler.setFormatter(self.formatter)


def create_logger():

    # Create a handler
    sh = logging.StreamHandler(sys.stdout)
    handler = logging.FileHandler(
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_revert_back_quotas.log",
        mode="w",
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)8s : %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
    )
    blank_formatter = logging.Formatter(fmt="")
    handler.setFormatter(formatter)

    # Create a logger, with the previously-defined handler
    logger = logging.getLogger("logging_test")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # Save some data and add a method to logger object

    logger.handler = handler
    logger.formatter = formatter
    logger.blank_formatter = blank_formatter
    logger.newline = types.MethodType(log_newline, logger)

    return logger


def display_current_values(namespace):

    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        quota = core_api.read_namespaced_resource_quota(f"{namespace}-quota", namespace)
        hard_limits = quota.spec.hard
        requests_cpu = hard_limits.get("requests.cpu")
        requests_memory = hard_limits.get("requests.memory")
        limits_cpu = hard_limits.get("limits.cpu")
        limits_memory = hard_limits.get("limits.memory")
        logger.info(f"Current resource quota values in namespace '{namespace}':")
        logger.info(f" - CPU Requests       : {requests_cpu} CPU")
        logger.info(f" - CPU Limits         : {limits_cpu} CPU")
        logger.info(f" - Memory Requests    : {requests_memory}")
        logger.info(f" - Memory Limits      : {limits_memory}")
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error retrieving resource quota '{namespace}-quota' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")


def patch_namespace_quota(namespace, quota_resource, value):

    quota_name = f"{namespace}-quota"

    # Prepare the patch body
    patch_body = {
        "spec": {
            "hard": {
                quota_resource: value
            }
        }
    }
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        core_api.patch_namespaced_resource_quota(
            name=quota_name,
            namespace=namespace,
            body=patch_body,
        )
        logger.info(
            f"Successfully patched resource quota '{quota_name}' in namespace '{namespace}'"
        )
        return True
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error patching resource quota '{quota_name}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")
        return False


def revert_back_original(namespace):

    # Specify the file path
    filepath = "./backups/"
    filename = f"{namespace}_quota_backup.yaml"
    fullpath = os.path.join(filepath, filename)

    if not os.path.exists(fullpath):
        logger.error(
            f"Backup file '{fullpath}' does not exist. Cannot revert resource quotas for namespace '{namespace}'."
        )
        logger.newline()
        return
    # Read the backup file
    with open(fullpath, "r") as file:
        try:
            backup_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"Error reading YAML file '{fullpath}': {e}")
            return
    if not backup_data or "spec" not in backup_data or "hard" not in backup_data["spec"]:
        logger.error(
            f"Invalid backup data in file '{fullpath}'. Cannot revert resource quotas for namespace '{namespace}'."
        )
        return  
    hard_limits = backup_data["spec"]["hard"]
    requests_cpu = hard_limits.get("requests.cpu")
    requests_memory = hard_limits.get("requests.memory")
    limits_cpu = hard_limits.get("limits.cpu")
    limits_memory = hard_limits.get("limits.memory")
    if not all([requests_cpu, requests_memory, limits_cpu, limits_memory]):
        logger.error(
            f"Missing resource quota values in backup file '{fullpath}'. Cannot revert resource quotas for namespace '{namespace}'."
        )
        return
    logger.info(f"Reverting resource quotas for namespace '{namespace}' to original values from backup.")
    logger.info("Original resource quota values from backup file:")
    logger.info(f" - CPU Requests       : {requests_cpu} CPU")
    logger.info(f" - CPU Limits         : {limits_cpu} CPU")
    logger.info(f" - Memory Requests    : {requests_memory}")
    logger.info(f" - Memory Limits      : {limits_memory}")
    
    logger.newline()
    display_current_values(namespace)


def check_quota(namespace):

    # Check if a resource quota exists in the given namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        quota = core_api.read_namespaced_resource_quota(f"{namespace}-quota", namespace)
        logger.info(f"Resource quota '{quota.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Resource quota '{namespace}-quota' not found in namespace '{namespace}'. Moving on !")
        else:
            logger.error(f"Error checking resource quota in namespace '{namespace}'")
            logger.error("Error details: ")
            logger.error(f" - Reason: {e.reason}")
            logger.error(f" - Status: {e.status}")
            logger.error(f" - Message: {e.body}")
        return False


def check_namespace(namespace):

    # Check if a namespace exists in the cluster.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        namespace = core_api.read_namespace(namespace)
        logger.info(f"Namespace '{namespace.metadata.name}' exists.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Namespace '{namespace}' not found. Moving on !")
        else:
            logger.error(f"Error checking namespace '{namespace}'")
            logger.error("Error details: ")
            logger.error(f" - Reason: {e.reason}")
            logger.error(f" - Status: {e.status}")
            logger.error(f" - Message: {e.body}")
        return False


def check_login():

    # Check if the user is logged in to the OpenShift cluster.
    # If not, prompt the user to log in and exit the script.
    try:
        subprocess.check_output(
            ["oc", "whoami"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        logger.error("UNAUTHORIZED...!! Please login to the cluster and try again... !")
        sys.exit(1)


def main():

    check_login()

    # Read SMMR configuration from the OpenShift cluster.
    output = subprocess.run(
        [
            "oc",
            "get",
            "smmr",
            "default",
            "-n",
            "istio-system",
            "-o",
            "yaml",
        ],
        capture_output=True,
    )
    smmr = yaml.safe_load(output.stdout)

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )
    logger.newline()

    members_list = smmr["spec"]["members"]

    for members in members_list:
        # Check if namespace exists
        if check_namespace(members):
            # Check if quota exists in the namespace
            if check_quota(members):
                # Revert back the resource quotas for the given namespace.
                revert_back_original(members)

            logger.info(
                "====================================================================================="
            )
            logger.newline()

    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()

    check_login()

    # Configure the Kubernetes client to connect to the OpenShift cluster.
    output = subprocess.run(
        ["oc", "whoami", "-t"],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error("Unable to set KUBERNETES_TOKEN environment variable. Exiting...")
        sys.exit(1)  # Exit if the token is not set
    else:
        os.environ["KUBERNETES_TOKEN"] = output.stdout.strip()

    # Configure the Kubernetes client
    configuration = client.Configuration()
    configuration.api_key_prefix = {"authorization": "Bearer"}
    configuration.api_key = {
        "authorization": os.environ.get("KUBERNETES_TOKEN", "")
    }  # Ensure the token is set in the environment variable
    if not configuration.api_key["authorization"]:
        logger.error("KUBERNETES_TOKEN environment variable is not set. Exiting...")
        sys.exit(1)  # Exit if the token is not set
    configuration.host = os.environ.get(
        "KUBERNETES_HOST", ""
    )  # Ensure the host is set in the environment variable
    if not configuration.host:
        logger.error("KUBERNETES_HOST environment variable is not set. Exiting...")
        sys.exit(1)  # Exit if the host is not set
    configuration.verify_ssl = (
        False  # Disable SSL verification for local testing; set to True in production
    )

    api_client = client.ApiClient(configuration)

    global core_api, apps_api  # Declare core_api and apps_api as global variables to use them in other functions
    core_api = client.CoreV1Api(api_client)
    apps_api = client.AppsV1Api(api_client)

    # Run the main function
    main()