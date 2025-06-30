#!/usr/bin/env python3
"""
Filename      : disable_smcp_gateway.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script disables smcp gateway by setting enabled: false in the servicemesh control plane configuration.
"""

import json
import logging
import os
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
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_disable_smcp_gateway.log",
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


def patch_smcp(gateway_type, gateway_id):

    patch_data = [
        {
            "op": "replace",
            "path": f"/spec/gateways/{gateway_type}/{gateway_id}/enabled",
            "value": False,
        }
    ]

    # Convert patch_data to a JSON string
    json_patch = json.dumps(patch_data)

    # Patch the SMCP configuration to disable the gateways.
    output = subprocess.run(
        [
            "oc",
            "patch",
            "smcp",
            "app-mesh-01",
            "-n",
            "istio-system",
            "--type=json",
            f"-p={json_patch}",
        ],
        capture_output=True,
    )

    if output.returncode != 0:
        logger.error("Failed to patch SMCP: %s", output.stderr.decode())
        sys.exit(1)
    else:
        logger.info("Successfully patched smcp: %s", patch_data)


def check_login():

    # Check if the user is logged in to the OpenShift cluster.
    # If not, prompt the user to log in and exit the script.
    try:
        proc = subprocess.check_output(
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
    logger.newline()

    gateway_list = smcp["spec"]["gateways"]

    for gateway_type in gateway_list:
        if gateway_type in ["additionalEgress", "additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id]["namespace"]

                logger.info(
                    "Disabling SMCP gateway: %s in namespace: %s", gateway_id, namespace
                )

                patch_smcp(gateway_type, gateway_id)

                logger.newline()

    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()
    main()