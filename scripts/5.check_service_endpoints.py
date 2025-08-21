#!/usr/bin/env python3
"""
Filename      : check_service_endpoints.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This scripts checks the service endpoints for injected gateways pods in an OpenShift cluster.
"""



import logging
import os
import subprocess
import sys
import types
from datetime import datetime
import kubernetes.client.rest
from kubernetes import client, config
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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_check_service_endpoints.log",
        mode="w",
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)8s : %(message)s", datefmt="%a, %d %b %Y %H:%M:%S"
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


def get_pod_ip(label_selector, namespace):
    
    # Get the pod IPs based on the label selector in the specified namespace.
    try:
        pods = core_api.list_namespaced_pod(namespace, label_selector=label_selector)
        if not pods.items:
            logger.warning(
                f"No pods found with label selector '{label_selector}' in namespace '{namespace}'."
            )
            return False
        
        pod_ip = {}
        for pod in pods.items:
            if pod.status.pod_ip:
                pod_ip[pod.metadata.name] = pod.status.pod_ip

        return pod_ip

    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error checking pods with label selector '{label_selector}' in namespace '{namespace}': {e}"
        )
        return False


def check_service_endpoints(service_name, namespace, pod_ip):

    # Check if the service endpoints are available for the given service in the specified namespace.
    try:
        endpoints = core_api.read_namespaced_endpoints(service_name, namespace)

        if not endpoints.subsets:
            logger.warning(
                f"Service '{service_name}' in namespace '{namespace}' has no endpoints."
            )
            return False
        
        # Check if any subset has addresses
        if any(subset.addresses for subset in endpoints.subsets):
            logger.info(
                f"Service '{service_name}' in namespace '{namespace}' has endpoints."
            )
            for k, v in pod_ip.items():
                if v in [
                    address.ip
                    for subset in endpoints.subsets
                    if subset.addresses
                    for address in subset.addresses
                ]:
                    logger.info(
                        f"Pod '{k}' with IP '{v}' is listed in the service '{service_name}' as READY endpoint."
                    )
                 # Check if any subset has not_ready_addresses
                elif v in [
                        address.ip
                        for subset in endpoints.subsets
                        if subset.not_ready_addresses
                        for address in subset.not_ready_addresses
                ]:
                        logger.warning(
                            f"Pod '{k}' with IP '{v}' is listed in the service '{service_name}' as NOT READY endpoint."
                        )
                else:
                    logger.warning(
                        f"Pod '{k}' with IP '{v}' is NOT listed in the service '{service_name}' as an endpoint."
                    )

    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error checking service '{service_name}' in namespace '{namespace}': {e}"
        )
        return False

def check_replicas_mismatch(namespace, deployment_name):

    # Check if the number of desired replicas matches the number of available replicas for a deployment.
    try:
        deployment = apps_api.read_namespaced_deployment(deployment_name, namespace)
        desired_replicas = deployment.spec.replicas
        available_replicas = deployment.status.available_replicas

        if desired_replicas != available_replicas:
            logger.warning(
                f"Replica mismatch for deployment '{deployment_name}' in namespace '{namespace}': "
                f"desired={desired_replicas}, available={available_replicas}"
            )
            return True
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error checking replicas for deployment '{deployment_name}' in namespace '{namespace}': {e}"
        )
    return False

def check_service_exists(namespace, service):

    # Check if a service exists in the given namespace.
    output = subprocess.run(
        ["oc", "get", "svc", service, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.warning(f"Service {service} does not exist in namespace {namespace}.")
        logger.newline()
        return False
    else:
        logger.info(f"Service {service} exists in namespace {namespace}.")
        return True


def check_namespace(namespace):

    # Check if a namespace exists.
    output = subprocess.run(
        ["oc", "get", "namespace", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(f"Namespace {namespace} does not exist.")
        return False
    logger.info(f"Namespace {namespace} exists.")
    return True


def check_deployment(namespace, gateway_id):

    # Check if a deployment exists in a given namespace.
    output = subprocess.run(
        ["oc", "get", "deployment", gateway_id, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.warning(
            f"Deployment {gateway_id} does not exist in namespace {namespace}. Moving on!"
        )
        return False
    logger.info(f"Deployment {gateway_id} exists in namespace {namespace}.")
    return True


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
                    deployment_name = f"{gateway_id}-gateway"
                    if check_deployment(namespace, deployment_name):
                        # Check if the service exists in the namespace
                        if check_service_exists(namespace, gateway_id):
                            # Check if the pod IPs are available
                            label_selector = f"type=injectedgateway, app={gateway_id}"
                            pod_ip = get_pod_ip(label_selector, namespace)
                            # Check if the service endpoints are available
                            if pod_ip:
                                check_service_endpoints(gateway_id, namespace, pod_ip)
                            else:
                                logger.warning(f"No valid pod IPs found for {gateway_id} in {namespace}.")

                            check_replicas_mismatch(namespace, deployment_name)

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

    config.load_kube_config()

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