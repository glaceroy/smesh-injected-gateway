"""
Filename      : increase_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will increase the resource quota memory and CPU by 1Gi and 1 Core respectively for the smesh namespace of the injected gateway.
"""

import logging
import os
import subprocess
import sys
import types
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import requests
import argparse
import operator

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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_increase_quotas.log",
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

    output = subprocess.run(
        [
            "oc",
            "get",
            "quota",
            f"{namespace}-quota",
            "-n",
            namespace,
            "-o",
            "yaml",
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(
            f"Failed to retrieve current resource quota for namespace '{namespace}': {output.stderr}"
        )
        return False

    logger.info("Resource quota AFTER UPDATE :")
    quota = yaml.safe_load(output.stdout)

    requests_cpu = quota["status"]["hard"].get("requests.cpu")
    requests_memory = quota["status"]["hard"].get("requests.memory")
    limits_cpu = quota["status"]["hard"].get("limits.cpu")
    limits_memory = quota["status"]["hard"].get("limits.memory")

    logger.info(f" - CPU Requests       : {requests_cpu} CPU")
    logger.info(f" - CPU Limits         : {limits_cpu} CPU")
    logger.info(f" - Memory Requests    : {requests_memory}")
    logger.info(f" - Memory Limits      : {limits_memory}")
    logger.newline()


def patch_namespace_quota(namespace, resources):

    quota_name = f"{namespace}-quota"

    if dry_run:
        # Simulate the patching action without executing it
        output = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f'oc patch quota {quota_name} -n {namespace} --type=merge -p \'{{"spec": {{"hard": {resources}}}}}\'',
            stderr="",
        )
        # Log the dry run output
        logger.info(f"DRY RUN Command: {output.stdout}")
    else:
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
                body={
                    "spec": {
                        "hard": {
                            **resources
                        }
                    }
                },
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
    output = subprocess.run(
        ["oc", "get", "quota", quota_name, "-n", namespace, "-o", "yaml"],
        capture_output=True,
        text=True,
    )
    quota = yaml.safe_load(output.stdout)

    requests_cpu = quota["status"]["hard"].get("requests.cpu")
    requests_cpu_unit = requests_cpu[-1:]

    requests_memory = quota["status"]["hard"].get("requests.memory")
    requests_memory_unit = requests_memory[-2:]

    limits_cpu = quota["status"]["hard"].get("limits.cpu")
    limits_cpu_unit = limits_cpu[-1:]

    limits_memory = quota["status"]["hard"].get("limits.memory")
    limits_memory_unit = limits_memory[-2:]

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

            logger.newline()
            if not dry_run:
                # Log the successful patching of the resource quota
                logger.info(
                    f"Resource Quota for namespace '{namespace}' has been updated successfully."
                )
                logger.newline()

                display_current_values(namespace)

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
        logger.info(f"Resource Quota '{quota.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Resource Quota '{namespace}-quota' not found in namespace '{namespace}'. Moving on !")
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
                # Calculating namespace resources
                calculate_namespace_resources(members)

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

    parser = argparse.ArgumentParser("increase_quotas")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the script in dry run mode without making any changes.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the script in execution mode and make changes.",
    )

    if len(sys.argv) != 2:
        logger.info("USAGE: python increase_quotas.py --dry-run (OR) --execute")
        logger.error("Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    dry_run = args.dry_run

    if dry_run:
        logger.info(
            "********************************************************************"
        )
        logger.info(
            "****       Running in DRY RUN MODE. No changes will be made.    ****"
        )
        logger.info(
            "********************************************************************"
        )
        logger.newline()
    
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