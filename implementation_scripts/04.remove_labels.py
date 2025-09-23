"""
Filename      : remove_labels.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script removes all existing labels from service and service accounts.
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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_remove_labels.log",
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


def check_role_exists(namespace, role):

    # Check if a role exists in the given namespace.
    try:
        role =  auth_api.read_namespaced_role(role, namespace)
        logger.info(f"Role '{role.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Role '{role}' not found in namespace '{namespace}'. Moving on !")
        else:
            logger.error(f"Error checking Role '{role}' in namespace '{namespace}'")
            logger.error("Error details: ")
            logger.error(f" - Reason: {e.reason}")
            logger.error(f" - Status: {e.status}")
            logger.error(f" - Message: {e.body}")
        return False
    
    
def remove_role_label(namespace, role, labels_to_remove):
    
    # Remove the SMCP operator ownership labels from the specified role in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    label: None for label in labels_to_remove
                }
            }
        }
        auth_api.patch_namespaced_role(
            name=role,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels removed successfully from Role '{role}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error removing labels from Role '{role}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")
        
        
def check_role_binding_exists(namespace, role_binding):
    
    # Check if a role binding exists in the given namespace.
    try:
        role_binding = auth_api.read_namespaced_role_binding(role_binding, namespace)
        logger.info(f"Role Binding '{role_binding.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Role Binding '{role_binding}' not found in namespace '{namespace}'. Moving on !")
        else:
            logger.error(f"Error checking Role Binding '{role_binding}' in namespace '{namespace}'")
            logger.error("Error details: ")
            logger.error(f" - Reason: {e.reason}")
            logger.error(f" - Status: {e.status}")
            logger.error(f" - Message: {e.body}")
        return False


def remove_role_binding_label(namespace, role_binding, labels_to_remove):

    # Remove the SMCP operator ownership labels from the specified role binding in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    label: None for label in labels_to_remove
                }
            }
        }
        auth_api.patch_namespaced_role_binding(
            name=role_binding,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels removed successfully from Role Binding '{role_binding}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error removing labels from Role Binding '{role_binding}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")


def check_sa_exists(namespace, service_account):

    # Check if a service account exists in the given namespace.
    try:
        sa = core_api.read_namespaced_service_account(service_account, namespace)
        logger.info(f"Service Account '{sa.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Service Account '{service_account}' not found in namespace '{namespace}'. Moving on !")
        else:
            logger.error(f"Error checking Service Account '{service_account}' in namespace '{namespace}'")
            logger.error("Error details: ")
            logger.error(f" - Reason: {e.reason}")
            logger.error(f" - Status: {e.status}")
            logger.error(f" - Message: {e.body}")
        return False
    
    
def remove_sa_label(namespace, service_account, labels_to_remove):
    
    # Remove the SMCP operator ownership labels from the specified service account in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    label: None for label in labels_to_remove
                }
            }
        }
        core_api.patch_namespaced_service_account(
            name=service_account,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels removed successfully from Service Account '{service_account}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error removing labels from Service Account '{service_account}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")


def remove_service_label(namespace, service, labels_to_remove):
    
    # Remove the SMCP operator ownership labels from the specified service in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    label: None for label in labels_to_remove
                }
            }
        }
        core_api.patch_namespaced_service(
            name=service,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels removed successfully from service '{service}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error removing labels from service '{service}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")


def check_service_exists(namespace, service):

    # Check if a service exists in the given namespace.
    try:
        service = core_api.read_namespaced_service(service, namespace)
        logger.info(f"Service '{service.metadata.name}' exists in namespace '{namespace}'.")
        return True
    except kubernetes.client.rest.ApiException as e:
        if e.status == 404:
            logger.warning(f"Service '{service}' not found in namespace '{namespace}'. Moving on !")
        else:
            logger.error(f"Error checking service '{service}' in namespace '{namespace}'")
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
    
    labels_to_remove = [
        "app.kubernetes.io/component",
        "app.kubernetes.io/instance",
        "app.kubernetes.io/managed-by",
        "app.kubernetes.io/name",
        "app.kubernetes.io/part-of",
        "app.kubernetes.io/version",
        "istio.io/rev",
        "maistra-version",
        "maistra.io/owner",
        "maistra.io/owner-name",
        "release"
    ]

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
                    if check_service_exists(namespace, gateway_id):
                        remove_service_label(namespace, gateway_id, labels_to_remove)
                        if check_sa_exists(namespace, f"{gateway_id}-service-account"):
                            remove_sa_label(namespace, f"{gateway_id}-service-account", labels_to_remove)
                            if check_role_exists(namespace, f"{gateway_id}-sds"):
                                remove_role_label(namespace, f"{gateway_id}-sds", labels_to_remove)
                                if check_role_binding_exists(namespace, f"{gateway_id}-sds"):
                                    remove_role_binding_label(namespace, f"{gateway_id}-sds", labels_to_remove)

                                    logger.newline()
                                    logger.info(
                                        "====================================================================================="
                                    )
                                else:
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