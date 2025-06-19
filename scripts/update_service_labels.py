#!/usr/bin/env python3
"""
Filename      : update_service-labels.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script removes the ownership labels in a service.
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

def remove_service_labels(namespace, service):

    # Remove specific labels from a service in the given namespace.

    log.info(f"Removing labels from service {service} in namespace {namespace}")
    output = subprocess.run(
        ["oc", "label", "svc", service, "-n", namespace, "--overwrite", "app.kubernetes.io/managed-by-"],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(f"Failed to remove labels from service {service} in namespace {namespace}: {output.stderr}")
        sys.exit(1)
    log.info(f"Labels removed from service {service} in namespace {namespace}")

def check_service_exists(namespace, service):
  
    # Check if a service exists in the given namespace.

    log.info(f"Checking if service {service} exists in namespace {namespace}")
    output = subprocess.run(
        ["oc", "get", "svc", service, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        log.error(f"Service {service} does not exist in namespace {namespace}.")
        return False
    log.info(f"Service {service} exists in namespace {namespace}.")
    return True

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

                # Check if namespace exists
                if check_namespace_exists(namespace):
                    # Check if deployment exists in the namespace
                    if check_service_exists(namespace, gateway_id):
                    # Remove service labels  
                        remove_service_labels(namespace, gateway_id):


if __name__ == "__main__":
    main()