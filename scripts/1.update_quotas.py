#!/usr/bin/env python3
"""
Filename      : update_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will increase the resource quota memory and CPU by 1Gi and 1 Core respectively for the smesh namespace of the injected gateway.
"""

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
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_update_quotas.log",
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


def patch_namespace_quota(namespace, quota_resource, value):

    quota_name = f"{namespace}-quota"

    logger.info(
        f"Patching resource quota for namespace {namespace} with {quota_resource} = {value}"
    )
    # Patch the resource quota for the namespace
    output = subprocess.run(
        [
            "oc",
            "patch",
            "quota",
            quota_name,
            "-n",
            namespace,
            "--type=merge",
            "-p",
            f'{{"spec": {{"hard": {{"{quota_resource}": "{value}"}}}}}}',
        ],
        capture_output=True,
        text=True,
    )


def calculate_namespace_resources(namespace):

    quota_name = f"{namespace}-quota"
    # Get the resource quota for the namespace.
    output = subprocess.run(
        ["oc", "get", "quota", quota_name, "-n", namespace, "-o", "yaml"],
        capture_output=True,
        text=True,
    )
    quota = yaml.safe_load(output.stdout)

    requests_cpu = quota["status"]["hard"].get("requests.cpu")
    if isinstance(requests_cpu, str):
        requests_cpu = int(requests_cpu)

    requests_memory = quota["status"]["hard"].get("requests.memory")
    if isinstance(requests_memory, str):
        requests_memory_unit = requests_memory[-2:]
        # We strip the unit and convert to int
        requests_memory = int(requests_memory.replace(requests_memory_unit, ""))

    limits_cpu = quota["status"]["hard"].get("limits.cpu")
    if isinstance(limits_cpu, str):
        limits_cpu = int(limits_cpu)

    limits_memory = quota["status"]["hard"].get("limits.memory")
    if isinstance(limits_memory, str):
        limits_memory_unit = limits_memory[-2:]
        # We strip the unit and convert to int
        limits_memory = int(limits_memory.replace(limits_memory_unit, ""))

    if requests_memory_unit == "Gi" and limits_memory_unit == "Gi":

        logger.newline()
        logger.info(f"Current Quota Values:")
        logger.info(f"Requests CPU: {requests_cpu} CPU")
        logger.info(f"Requests Mem: {requests_memory}{requests_memory_unit} Memory")
        logger.info(f"Limits CPU: {limits_cpu} CPU")
        logger.info(f"Limits Mem: {limits_memory}{limits_memory_unit} Memory")

        requests_cpu = (
            requests_cpu + 1
        )  # Incrementing by 1 Core for the injected gateway
        requests_memory = (
            requests_memory + 1
        )  # Incrementing by 1Gi for the injected gateway
        limits_cpu = limits_cpu + 1  # Incrementing by 1 for the injected gateway
        limits_memory = (
            limits_memory + 1
        )  # Incrementing by 1Gi for the injected gateway

        logger.newline()

        resources = {
            "limits.cpu": limits_cpu,
            "limits.memory": str(limits_memory) + limits_memory_unit,
            "requests.cpu": requests_cpu,
            "requests.memory": str(requests_memory) + requests_memory_unit,
        }

        for resource, value in resources.items():
            patch_namespace_quota(namespace, resource, value)

        logger.newline()
        logger.info(f"Updated Quota Values:")
        logger.info(f"Requests CPU: {requests_cpu} CPU")
        logger.info(f"Requests Mem: {requests_memory}{requests_memory_unit} Memory")
        logger.info(f"Limits CPU: {limits_cpu} CPU")
        logger.info(f"Limits Mem: {limits_memory}{limits_memory_unit} Memory")

        logger.newline()
        logger.info(f"Result: Success for namespace {namespace}. Resource Quota has been updated.")
    else:
        logger.newline()
        logger.warning(f"Hard Memory units for requests and limits not in Gi.")
        logger.warning(
            f"Result: Fail for namespace {namespace}. Manual intervention required to update the quota."
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
        if gateway_type in ["additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                namespace = smcp["spec"]["gateways"][gateway_type][gateway_id][
                    "namespace"
                ]

                logger.newline()
                # Check if namespace exists
                if check_namespace(namespace):
                    calculate_namespace_resources(namespace)

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
    main()