#!/usr/bin/env python3
"""
Filename      : scale_down_smcp_gateway.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script scales down the replicas of the SMCP gateways
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
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_scale_down_smcp_gateway.log",
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


def scale_down_replicas(namespace, gateway):

    replicas = 0  # Set replicas to 0 to scale down

    # If dry run is enabled, just log the action and return.
    if dry_run:
        logger.info(
            f"DRY RUN: Would scale down replicas of {gateway} in namespace {namespace}"
        )
        # Simulate the command output for dry run
        output = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"oc scale deployment {gateway} --replicas {replicas} -n {namespace}",
        )
        logger.info(f"DRY RUN Command: {output.stdout}")
    else:
        # Set the expected number of replicas for a given gateway.
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
            logger.error(
                f"Failed to scale deployment in namespace {namespace}: {output.stderr}"
            )
            sys.exit(1)

        logger.info(
            f"Scaled deployment {gateway} to {replicas} replicas"
        )


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
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id]["namespace"]

                logger.newline()
                # Check if namespace exists
                if check_namespace(namespace):
                    # Check if deployment exists in the namespace
                    if check_deployment(namespace, gateway_id):
                        scale_down_replicas(namespace, gateway_id)

    logger.newline()
    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()

    parser = argparse.ArgumentParser("scale_down_smcp_gateway")
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
        logger.info("USAGE: python scale_down_smcp_gateway.py --dry-run (OR) --execute")
        logger.error("Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    dry_run = args.dry_run
    if dry_run:
        logger.info("Running in DRY RUN MODE. No changes will be made.")

    main()