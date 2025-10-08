"""
Filename      : adhoc_quota_increase.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will increase the resource quota memory and CPU for a list of namespaces provided in a file
"""

import argparse
import logging
import operator
import os
import subprocess
import sys
import types
from datetime import datetime

import kubernetes.client.rest
import requests
import yaml
from kubernetes import client
from urllib3.exceptions import InsecureRequestWarning


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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_adhoc_quota_increase.log",
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


def display_current_values(namespace, quota_name):

    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        quota = core_api.read_namespaced_resource_quota(quota_name, namespace)
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error retrieving resource quota '{quota_name}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")
        return

    requests_cpu = quota.spec.hard.get("requests.cpu")
    requests_memory = quota.spec.hard.get("requests.memory")
    limits_cpu = quota.spec.hard.get("limits.cpu")
    limits_memory = quota.spec.hard.get("limits.memory")
    logger.info(f" - CPU Requests       : {requests_cpu}")
    logger.info(f" - CPU Limits         : {limits_cpu}")
    logger.info(f" - Memory Requests    : {requests_memory}")
    logger.info(f" - Memory Limits      : {limits_memory}")


def patch_namespace_quota(namespace, resources):

    quota_name = f"{namespace}-quota"

    # Log the action of patching the resource quota
    logger.info(
        f"Patching resource quota for namespace '{namespace}' with '{resources}'"
    )
    # Patch the resource quota for the namespace
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        core_api.patch_namespaced_resource_quota(
            name=quota_name,
            namespace=namespace,
            body={"spec": {"hard": {**resources}}},
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error patching resource quota '{quota_name}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")


def calculate_namespace_resources(namespace):

    update_cpu_unit = 2  # Increment CPU by 2 Core for the injected gateway
    update_memory_unit = 4  # Increment Memory by 4Gi for the injected gateway

    op_func = operator.add

    quota_name = f"{namespace}-quota"

    # Get the resource quota for the namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        quota = core_api.read_namespaced_resource_quota(quota_name, namespace)
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error retrieving resource quota '{quota_name}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")
        return

    requests_cpu = quota.spec.hard.get("requests.cpu")
    requests_memory = quota.spec.hard.get("requests.memory")
    limits_cpu = quota.spec.hard.get("limits.cpu")
    limits_memory = quota.spec.hard.get("limits.memory")
    requests_memory_unit = (
        "".join(filter(str.isalpha, requests_memory)) if requests_memory else None
    )
    limits_memory_unit = (
        "".join(filter(str.isalpha, limits_memory)) if limits_memory else None
    )
    requests_cpu_unit = (
        "".join(filter(str.isalpha, requests_cpu)) if requests_cpu else None
    )
    limits_cpu_unit = "".join(filter(str.isalpha, limits_cpu)) if limits_cpu else None

    if (
        requests_memory_unit == "Gi"
        and limits_memory_unit == "Gi"
        and requests_cpu_unit != "m"
        and limits_cpu_unit != "m"
    ):

        if isinstance(requests_cpu, str):
            requests_cpu = int(requests_cpu)

        if isinstance(requests_memory, str):
            # We strip the unit and convert to int
            requests_memory = int(requests_memory.replace(requests_memory_unit, ""))

        if isinstance(limits_cpu, str):
            limits_cpu = int(limits_cpu)

        if isinstance(limits_memory, str):
            # We strip the unit and convert to int
            limits_memory = int(limits_memory.replace(limits_memory_unit, ""))

            logger.newline()
            logger.info("Resource quota BEFORE UPDATE :")
            logger.info(f" - CPU Requests       : {requests_cpu} CPU")
            logger.info(f" - CPU Limits         : {limits_cpu} CPU")
            logger.info(
                f" - Memory Requests    : {requests_memory}{requests_memory_unit}"
            )
            logger.info(f" - Memory Limits      : {limits_memory}{limits_memory_unit}")

            requests_cpu = op_func(requests_cpu, update_cpu_unit)
            limits_cpu = op_func(limits_cpu, update_cpu_unit)
            requests_memory = op_func(requests_memory, update_memory_unit)
            limits_memory = op_func(limits_memory, update_memory_unit)

            logger.newline()

            resources = {
                "requests.cpu": requests_cpu,
                "limits.cpu": limits_cpu,
                "requests.memory": str(requests_memory) + requests_memory_unit,
                "limits.memory": str(limits_memory) + limits_memory_unit,
            }

            patch_namespace_quota(namespace, resources)
            display_current_values(namespace, quota_name)

    else:
        logger.newline()
        logger.warning("Resource quotas not defined in Gi or Core")
        logger.warning(
            f"Result: Fail for namespace '{namespace}'. Manual intervention required to update the quota."
        )
        logger.newline()


def check_quota(namespace):

    # Check if a resource quota exists in the namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        quota = core_api.read_namespaced_resource_quota(f"{namespace}-quota", namespace)
        logger.info(
            f"Resource Quota '{quota.metadata.name}' exists in namespace '{namespace}'."
        )
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(
                f"Resource Quota '{namespace}-quota' not found in namespace '{namespace}'. Moving on !"
            )
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

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )
    logger.newline()

    # Read the list of namespaces from the input file
    try:
        with open(input_file, "r") as f:
            members_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"Input file '{input_file}' not found. Exiting...")
        sys.exit(1)
    logger.info(f"Total namespaces to process: {len(members_list)}")
    logger.newline()
    logger.info(
        "========================================================================================"
    )
    logger.newline()

    for members in members_list:
        # Check if namespace exists
        if check_namespace(members):
            # Check if quota exists in the namespace
            if check_quota(members):
                # Calculating namespace resources
                calculate_namespace_resources(members)

            logger.newline()
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

    parser = argparse.ArgumentParser("adhoc_quota_increase")

    if len(sys.argv) != 2:
        logger.info("USAGE: python adhoc_quota_increase.py <namespace_file>")
        logger.error("Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    input_file = sys.argv[1]

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