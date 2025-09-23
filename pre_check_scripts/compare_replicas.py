#!/usr/bin/env python3
"""
Filename      : compare_replicas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script compares the replicas defined in the cluster values file and what is currently running for each gateway.
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

import yaml


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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_compare_replicas.log",
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


def get_total_namespaces():

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
    members_list = smmr["spec"]["members"]

    return len(members_list)


def get_values_replicas(ns, gateway_type, values_file):

    replicas = None

    # Read the replicas for a given gateway from the values file.
    with open(values_file, "r") as f:
        cluster_values = yaml.safe_load(f)

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

    # Get the current number of replicas for a given deployment in a given namespace.
    try:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        deployment = apps_api.read_namespaced_deployment(gateway_id, namespace)
        replicas = deployment.spec.replicas
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
    smcp = yaml.safe_load(output.stdout)

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )

    namespace_mismatch = 0
    ns_list = []

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
                            ns_list.append({namespace: gateway_id})
                            logger.error(
                                f"MISMATCH - Replicas for deployment {gateway_id} in namespace {namespace}"
                            )
                            logger.error(f"  - Cluster has {cluster_replicas} replicas")
                            logger.error(
                                f"  - Values file has {values_replicas} replicas"
                            )

                        else:
                            logger.info(
                                f"MATCH - Replicas for deployment {gateway_id} in namespace {namespace}"
                            )
                            logger.info(f"  - Cluster has {cluster_replicas} replicas")
                            logger.info(
                                f"  - Values file has {values_replicas} replicas"
                            )

                        logger.newline()
                        logger.info(
                            "====================================================================================="
                        )

    total_namespaces = get_total_namespaces()

    # sorting the list of namespaces with mismatches
    ns_list = sorted(ns_list, key=lambda x: list(x.keys())[0])

    namespace_mismatch = len(set([list(item.keys())[0] for item in ns_list]))

    logger.newline()
    logger.info(
        f"Total servicemesh member namespaces in the cluster: {total_namespaces}"
    )
    logger.info(
        f"Total servicemesh member namespaces with replica mismatches: {namespace_mismatch}"
    )
    logger.newline()
    logger.info(f"\t\t{'NAMESPACE':<50}\t{' : ':<2}\t{'GATEWAY_ID':<10}")
    for item in ns_list:
        logger.info(
            f"\t\t{list(item.keys())[0]:<50}\t{' : ':<2}\t{list(item.values())[0]:<10}"
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
        logger.info("USAGE: python compare_replicas.py <cluster_values.yaml>")
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