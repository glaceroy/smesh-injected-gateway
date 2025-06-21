#!/usr/bin/env python3
"""
Filename      : update_gateway_replicas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script updates the number of replicas for injected gateways based on the servicemesh control plane gateway replicas for a given namespace.
"""

import logging as log
from datetime import datetime
import os
import subprocess
import sys
import yaml

# Create a logger object
logger = log.getLogger("")
logger.setLevel(log.INFO)
sh = log.StreamHandler(sys.stdout)
# Set up a rotating file handler
handler = log.FileHandler(
    '{}_update_gateway_replicas.log'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')),
    mode='w',
    encoding='utf-8',
)

formatter = log.Formatter(
    "[%(asctime)s] %(levelname)8s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
handler.setFormatter(formatter)
# Add the handler to the logger
logger.addHandler(handler)
sh.setFormatter(formatter)
#sh.addHandler(handler)
logger.addHandler(sh)

#width = os.get_terminal_size().columns 

def set_expected_replicas(namespace, replicas, gateway):

    # Set the expected number of replicas for a given gateway.

    #log.info(f"Setting expected replicas for namespace {namespace} with current replicas {replicas}")

    output = subprocess.run(
        [
            "oc",
            "scale",
            "deployment",
            gateway,
            "--replicas",
            str(replicas),
            "-n",
            namespace,
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(
            f"Failed to scale deployment in namespace {namespace}: {output.stderr}"
        )
        sys.exit(1)

    log.info(f"Scaled deployment {gateway} in namespace {namespace} to {replicas} replicas")


def get_current_replicas(namespace, gateway_id):

    # Get the current number of replicas for a given gateway.

    # log.info(f"Getting current replicas for gateway {gateway_id} in namespace {namespace}")

    output = subprocess.run(
        [
            "oc",
            "get",
            "deployment",
            gateway_id,
            "-n",
            namespace,
            "-o",
            "jsonpath={.spec.replicas}",
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(
            f"Failed to get replicas for gateway {gateway_id} in namespace {namespace}: {output.stderr}"
        )
        sys.exit(1)
    try:
        current_replicas = int(output.stdout.strip())
    except ValueError:
        log.error(
            f"Failed to parse replicas for gateway {gateway_id} in namespace {namespace}: {output.stdout}"
        )
        sys.exit(1)
    log.info(
        f"Current replicas for gateway {gateway_id} in namespace {namespace} is: {current_replicas}"
    )
    return current_replicas


def check_namespace_exists(namespace):

    # Check if a namespace exists.

    #log.info(f"Checking if namespace {namespace} exists")
    output = subprocess.run(
        ["oc", "get", "namespace", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(f"Namespace {namespace} does not exist.")
        return False
    log.info(f"Namespace {namespace} exists.")
    return True


def check_deployment_exists(namespace, gateway_id):

    # Check if a deployment exists in a given namespace.

    #log.info(f"Checking if deployment {gateway_id} exists in namespace {namespace}")
    output = subprocess.run(
        ["oc", "get", "deployment", gateway_id, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.warning(f"Deployment {gateway_id} does not exist in namespace {namespace}. Moving on!")
        return False
    log.info(f"Deployment {gateway_id} exists in namespace {namespace}.")
    return True

def check_login():

    try:
        proc = subprocess.check_output(
            ["oc", "whoami"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        log.error("UNAUTHORIZED...!! Please login to the cluster and try again... !")
        sys.exit(1)

    log.info("Already logged in. Using existing login session.. !")

def main():

    # Check if the user is logged in to the OpenShift cluster.
    # If not, prompt the user to log in and exit the script.
    check_login()

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

    #print(' Starting Script Execution. '.center(width, '*'))

    gateway_list = smcp["spec"]["gateways"]

    for gateway_type in gateway_list:
        if gateway_type in ["additionalEgress", "additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id]["namespace"]

                #print("")
                #print('-' * width)
                #print("")

                # Check if namespace exists
                if check_namespace_exists(namespace):
                    # Check if deployment exists in the namespace
                    if check_deployment_exists(namespace, gateway_id):
                        # Get current replicas
                        current_replicas = get_current_replicas(namespace, gateway_id)

                        if gateway_type == "additionalIngress":
                            gateway_name = "injected-gateway-ingress"
                        else:
                            gateway_name = "injected-gateway-egress"

                        if check_deployment_exists(namespace, gateway_name):
                            # Set expected replicas
                            set_expected_replicas(namespace, current_replicas, gateway_name)

    #print("")
    #print(' End of Script Execution. '.center(width, '*'))

if __name__ == "__main__":
    main()