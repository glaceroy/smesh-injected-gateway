#!/usr/bin/env python3
"""
Filename      : remove_service_labels.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script removes the ownership labels in a service.
"""

import argparse
import logging
import subprocess
import sys
import types
from datetime import datetime

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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_remove_service_labels.log",
        mode="w",
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)8s : %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
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


def validate_label_removal(namespace, service):

    # Validate that the labels have been removed from the service.
    output = subprocess.run(
        ["oc", "get", "svc", service, "-n", namespace, "-o", "yaml"],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(
            f"Failed to get service {service} in namespace {namespace}: {output.stderr}"
        )
        sys.exit(1)

    service_data = yaml.safe_load(output.stdout)
    labels = service_data.get("metadata", {}).get("labels", {})

    if "app.kubernetes.io/managed-by" not in labels:
        logger.info(
            f"Validation Complete - SMCP OWnership Label successfully removed from service {service} in namespace {namespace}"
        )
    else:
        logger.error(
            f"SMCP OWnership Label still present on service {service} in namespace {namespace}"
        )

    logger.newline()


def remove_service_labels(namespace, service):

    # If dry run is enabled, just log the action and return.
    if dry_run:
        logger.info(
            f"DRY RUN: Would remove labels from service {service} in namespace {namespace}"
        )
        # Simulate the command output for dry run
        output = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"oc label svc {service} -n {namespace} --overwrite app.kubernetes.io/managed-by-",
        )
        logger.info(f"DRY RUN Command: {output.stdout}")
    else:
        # Remove specific labels from a service in the given namespace.
        output = subprocess.run(
            [
                "oc",
                "label",
                "svc",
                service,
                "-n",
                namespace,
                "--overwrite",
                "app.kubernetes.io/managed-by-",
            ],
            capture_output=True,
            text=True,
        )
        if output.returncode != 0:
            logger.error(
                f"Failed to remove SMCP Ownership label from service {service} in namespace {namespace}: {output.stderr}"
            )
            sys.exit(1)
        else:
            logger.info(
                f"SMCP OWnership Label removed from service {service} in namespace {namespace}"
            )


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


def check_namespace_exists(namespace):

    # Check if a namespace exists.

    output = subprocess.run(
        ["oc", "get", "namespace", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.warning(f"Namespace {namespace} does not exist.")
        logger.newline()
        return False
    else:
        logger.info(f"Namespace {namespace} exists.")
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

    check_login()

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
                if check_namespace_exists(namespace):
                    # Check if deployment exists in the namespace
                    if check_service_exists(namespace, gateway_id):
                        # Remove service labels
                        remove_service_labels(namespace, gateway_id)
                        validate_label_removal(namespace, gateway_id)

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

    parser = argparse.ArgumentParser("remove_service_labels")
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
        logger.info("USAGE: python remove_service_labels.py --dry-run (OR) --execute")
        logger.error("Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    dry_run = args.dry_run
    if dry_run:
        logger.info("Running in DRY RUN MODE. No changes will be made.")

    main()