#!/usr/bin/env python3
"""
Filename      : update_cluster_config_replicas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script updates the replicas defined in the cluster values file to match what is currently running for each gateway.
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
from kubernetes import client

from ruamel.yaml import YAML

yaml = YAML()
yaml.width = sys.maxsize  # Set width to max size to avoid line breaks in YAML output
yaml.preserve_quotes = True  # Preserve quotes in YAML output


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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_update_cluster_config_replicas.log",
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


def update_cluster_values(ns, gateway_type, values_file, replicas):

    # Update the replicas for a given gateway in the values file.
    with open(values_file, "r") as f:
        cluster_values = yaml.load(f)

    for ns_index, namespace in enumerate(cluster_values["project"]):
        if ns == namespace["namespace"]:
            for index, key in enumerate(namespace):
                if gateway_type == "additionalEgress":
                    cluster_values["project"][ns_index]["egress"]["replicas"] = replicas
                else:
                    cluster_values["project"][ns_index]["ingress"][
                        "replicas"
                    ] = replicas

    with open(values_file, "w") as f:
        yaml.dump(cluster_values, f)


def get_values_replicas(ns, gateway_type, values_file):

    replicas = None

    # Read the replicas for a given gateway from the values file.
    with open(values_file, "r") as f:
        cluster_values = yaml.load(f)

    for ns_index, namespace in enumerate(cluster_values["project"]):
        if ns == namespace["namespace"]:
            for index, key in enumerate(namespace):
                if gateway_type == "additionalEgress":
                    replicas = cluster_values["project"][ns_index]["egress"]["replicas"]
                else:
                    replicas = cluster_values["project"][ns_index]["ingress"][
                        "replicas"
                    ]

    return replicas


def get_cluster_replicas(namespace, gateway_id):

    # Get the current number of replicas for a given deployment in a namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        deployment = apps_api.read_namespaced_deployment(gateway_id, namespace)
        replicas = deployment.spec.replicas
        logger.info(
            f"Current replicas for deployment '{gateway_id}' in namespace '{namespace}': {replicas}"
        )
        return replicas
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error getting replicas for deployment '{gateway_id}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")
        return None


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


def check_deployment(namespace, gateway_id):

    # Check if a deployment exists in a given namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        deployment = apps_api.read_namespaced_deployment(gateway_id, namespace)
        logger.info(
            f"Deployment '{deployment.metadata.name}' exists in namespace '{namespace}'."
        )
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(
                f"Deployment '{gateway_id}' not found in namespace '{namespace}'. Moving on !"
            )
        else:
            logger.error(
                f"Error checking deployment '{gateway_id}' in namespace '{namespace}'"
            )
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

    if not os.path.isfile(values_file):
        logger.error(f"Required input file {values_file} does not exist. Exiting.. !")
        sys.exit(1)

    # Read SMCP configuration from the OpenShift cluster.
    output = subprocess.run(
        [
            "oc",
            "get",
            "smcp",
            "app-mesh-01",
            "-n",
            "istio-system",
            "-o",
            "yaml",
        ],
        capture_output=True,
    )
    smcp = yaml.load(output.stdout)

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )

    gateway_list = smcp["spec"]["gateways"]

    for gateway_type in gateway_list:
        if gateway_type in ["additionalEgress", "additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id][
                    "namespace"
                ]

                logger.newline()
                # Check if namespace exists
                if check_namespace(namespace):
                    # Check if deployment exists in the namespace
                    if check_deployment(namespace, gateway_id):
                        # Get current replicas
                        cluster_replicas = get_cluster_replicas(namespace, gateway_id)
                        values_replicas = get_values_replicas(
                            namespace, gateway_type, values_file
                        )
                        if cluster_replicas != values_replicas:
                            logger.warning(
                                f"Mismatch found for deployment {gateway_id} in namespace {namespace}:"
                            )
                            update_cluster_values(
                                namespace, gateway_type, values_file, cluster_replicas
                            )
                            logger.info(
                                f"Updated replicas from {values_replicas} to {cluster_replicas} for deployment {gateway_id} in namespace {namespace} in cluster values file"
                            )
                        else:
                            logger.info(
                                f"Replicas match for deployment {gateway_id} in namespace {namespace}: {cluster_replicas}"
                            )
                            logger.info("No update needed.")

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
        
        
    # Check if two arguments are provided (not counting the script name)
    if len(sys.argv) != 2:
        logger.info("USAGE: python update_cluster_config_replicas.py <cluster_values.yaml>")
        logger.error("Please provide full path for the cluster values file.")
        sys.exit(1)  # Exit with error status

    values_file = sys.argv[1]

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

    global core_api, apps_api, auth_api  # Declare core_api and apps_api as global variables to use them in other functions
    core_api = client.CoreV1Api(api_client)
    apps_api = client.AppsV1Api(api_client)
    auth_api = client.RbacAuthorizationV1Api(api_client)

    # Run the main function
    main()