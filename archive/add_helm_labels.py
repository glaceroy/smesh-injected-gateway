"""
Filename      : add_helm_adoption_labels.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script adds Helm adoption labels to services and service accounts.
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
    
    
def apply_role_label(namespace, role):

    # Apply Helm management labels to the specified role in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/managed-by": "Helm"
                },
                "annotations": {
                    "meta.helm.sh/release-name": "service-mesh-injected-gateway",
                    "meta.helm.sh/release-namespace": "istio-system"
                }
            }
        }
        auth_api.patch_namespaced_role(
            name=role,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels added successfully to Role '{role}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error adding labels to Role '{role}' in namespace '{namespace}'"
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
    
    
def apply_role_binding_label(namespace, role_binding):

    # Apply Helm management labels to the specified role binding in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/managed-by": "Helm"
                },
                "annotations": {
                    "meta.helm.sh/release-name": "service-mesh-injected-gateway",
                    "meta.helm.sh/release-namespace": "istio-system"
                }
            }
        }
        auth_api.patch_namespaced_role_binding(
            name=role_binding,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels added successfully to Role Binding '{role_binding}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error adding labels to Role Binding '{role_binding}' in namespace '{namespace}'"
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
    
    
def apply_sa_label(namespace, service_account):
    
    # Apply Helm management labels to the specified service account in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/managed-by": "Helm"
                },
                "annotations": {
                    "meta.helm.sh/release-name": "service-mesh-injected-gateway",
                    "meta.helm.sh/release-namespace": "istio-system"
                }
            }
        }
        core_api.patch_namespaced_service_account(
            name=service_account,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels added successfully to Service Account '{service_account}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error adding labels to Service Account '{service_account}' in namespace '{namespace}'"
        )
        logger.error("Error details: ")
        logger.error(f" - Reason: {e.reason}")
        logger.error(f" - Status: {e.status}")
        logger.error(f" - Message: {e.body}")

def add_service_label(namespace, service):
    
    # Remove the SMCP operator ownership labels from the specified service in the given namespace.
    try:
        body = {
            "metadata": {
                "labels": {
                    "app.kubernetes.io/managed-by": "Helm"
                },
                "annotations": {
                    "meta.helm.sh/release-name": "service-mesh-injected-gateway",
                    "meta.helm.sh/release-namespace": "istio-system"
                }
            }
        }
        core_api.patch_namespaced_service(
            name=service,
            namespace=namespace,
            body=body,
        )
        logger.info(
            f"Labels added successfully to service '{service}' in namespace '{namespace}'."
        )
    except kubernetes.client.rest.ApiException as e:
        logger.error(
            f"Error adding labels to service '{service}' in namespace '{namespace}'"
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

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )

    files = [file1, file2]
    # Check if the required files exist
    for file in files:
        if os.path.isfile(file):
            logger.info(f"The required file {file} exists.")
        else:
            logger.error(f"Required input file {file} does not exist. Exiting.. !")
            logger.newline()
            sys.exit(1)

    # Read input namespace yaml file
    with open(file1, "r") as ns_stream:
        ns_list = yaml.load(ns_stream)

    # Read cluster values yaml file
    for ns in ns_list:
        with open(file2, "r") as cv_stream:
            cluster_values = yaml.load(cv_stream)

        # Check if the namespace exists in the cluster values
        if "project" not in cluster_values:
            logger.error(
                "The cluster values file does not contain 'project' key. Exiting.. !"
            )
            logger.error(
                "Check the order of input files passed to the script. Exiting.. !"
            )
            logger.info(
                "USAGE: python add_helm_adoption_labels.py <input_namespace.yaml> <cluster_values.yaml>"
            )
            logger.newline()
            sys.exit(1)

        for ns_index, namespace in enumerate(cluster_values["project"]):
            if ns == namespace["namespace"]:
                for index, key in enumerate(namespace):
                    if key == "egress":
                        gw_id = cluster_values["project"][ns_index]["egress"]["id"]
                        if check_namespace(ns):
                            if check_service_exists(ns, f"eg{gw_id}"):
                                add_service_label(ns, f"eg{gw_id}")
                            if check_sa_exists(ns, f"eg{gw_id}-service-account"):
                                apply_sa_label(ns, f"eg{gw_id}-service-account")
                            if check_role_exists(ns, f"eg{gw_id}-sds"):
                                apply_role_label(ns, f"eg{gw_id}-sds")
                            if check_role_binding_exists(ns, f"eg{gw_id}-sds"):
                                apply_role_binding_label(ns, f"eg{gw_id}-sds")

                    elif key == "ingress":
                        gw_id = cluster_values["project"][ns_index]["ingress"]["id"]
                        if check_namespace(ns):
                            if check_service_exists(ns, f"ig{gw_id}"):
                                add_service_label(ns, f"ig{gw_id}")
                            if check_sa_exists(ns, f"ig{gw_id}-service-account"):
                                apply_sa_label(ns, f"ig{gw_id}-service-account")
                            if check_role_exists(ns, f"ig{gw_id}-sds"):
                                apply_role_label(ns, f"ig{gw_id}-sds")
                            if check_role_binding_exists(ns, f"ig{gw_id}-sds"):
                                apply_role_binding_label(ns, f"ig{gw_id}-sds")

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
    
    # Check if two arguments are provided (not counting the script name)
    if len(sys.argv) != 3:
        logger.info(
            "USAGE: python add_helm_adoption_labels.py <input_namespace.yaml> <cluster_values.yaml>"
        )
        logger.error("Please provide full path for the two input values.")
        sys.exit(1)  # Exit with error status

    # Assign values
    file1 = sys.argv[1]
    file2 = sys.argv[2]

    # Run the main function
    main()