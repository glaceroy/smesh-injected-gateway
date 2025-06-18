#!/usr/bin/env python3
"""
Filename      : update_gateway_replicas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script updates the number of replicas for injected gateways based on the servicemesh control plane gateway replicas.
"""

import logging as log
import os
import subprocess
import sys
import yaml

logger = log.getLogger("")
logger.setLevel(log.DEBUG)
sh = log.StreamHandler(sys.stdout)
formatter = log.Formatter(
    "[%(asctime)s] %(levelname)s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
sh.setFormatter(formatter)
logger.addHandler(sh)

def set_expected_replicas(namespace, replicas, gateway):
    
    # Set the expected number of replicas for a given gateway.

    log.info(f"Setting expected replicas for namespace {namespace} with current replicas {replicas}")

    output = subprocess.run(
        [
            "oc",
            "scale",
            "deployment",
            "injected-gateway-" + gateway,
            "--replicas",
            str(replicas),
            "-n",
            namespace,
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(f"Failed to scale deployment in namespace {namespace}: {output.stderr}")
        sys.exit(1)
    
    log.info(f"Scaled deployment in namespace {namespace} to {replicas} replicas") 

def get_current_replicas(namespace, gateway_id):

    # Get the current number of replicas for a given gateway.

    log.info(f"Getting current replicas for gateway {gateway_id} in namespace {namespace}")
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
        log.error(f"Failed to get replicas for gateway {gateway_id} in namespace {namespace}: {output.stderr}")
        sys.exit(1)
    try:
        current_replicas = int(output.stdout.strip())
    except ValueError:
        log.error(f"Failed to parse replicas for gateway {gateway_id} in namespace {namespace}: {output.stdout}")
        sys.exit(1)
    log.info(f"Current replicas for gateway {gateway_id} in namespace {namespace}: {current_replicas}")
    return current_replicas 

def check_namespace_exists(namespace):

    # Check if a namespace exists.

    log.info(f"Checking if namespace {namespace} exists")
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

    log.info(f"Checking if deployment {gateway_id} exists in namespace {namespace}")
    output = subprocess.run(
        ["oc", "get", "deployment", gateway_id, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(f"Deployment {gateway_id} does not exist in namespace {namespace}.")
        return False
    log.info(f"Deployment {gateway_id} exists in namespace {namespace}.")
    return True

def main():

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

    gateway_list = smcp["spec"]["gateways"]

    for gateway_type in gateway_list:
        if gateway_type in ["additionalEgress", "additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id]["namespace"]

                if gateway_type == "additionalIngress":
                    gateway = "ingress"
                else:
                    gateway = "egress"

                log.info("*****************************************************************************************")
                # Check if namespace exists
                check_namespace_exists(namespace)

                # Check if deployment exists in the namespace
                check_deployment_exists(namespace, gateway_id)
                
                # Get current replicas
                current_replicas = get_current_replicas(namespace, gateway_id)

                # Set expected replicas
                expected_replicas = set_expected_replicas(namespace, current_replicas, gateway)

if __name__ == "__main__":
    main()
