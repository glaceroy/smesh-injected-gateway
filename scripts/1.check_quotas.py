#!/usr/bin/env python3
"""
Filename      : check_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script evaluates if there is enough compute resources available
                in the namespaces resource quota to deploy injected.
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
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_check_quotas.py.log",
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


def calculate_namespace_resources(namespace):

    quota_name = f"{namespace}-quota"
    # Get the resource quota for the namespace.
    output = subprocess.run(
        ["oc", "get", "quota", quota_name, "-n", namespace, "-o", "yaml"],
        capture_output=True,
        text=True,
    )
    quota = yaml.safe_load(output.stdout)

    total_requests_cpu = quota["status"]["hard"].get("requests.cpu")
    total_requests_memory = quota["status"]["hard"].get("requests.memory")
    total_limits_cpu = quota["status"]["hard"].get("limits.cpu")
    total_limits_memory = quota["status"]["hard"].get("limits.memory")

    logger.info(f"TOTAL Resource quota:")
    logger.info(f"Total Requests CPU: {total_requests_cpu} CPU")
    logger.info(f"Total Requests Mem: {total_requests_memory} Memory")
    logger.info(f"Total Limits CPU: {total_limits_cpu} CPU")
    logger.info(f"Total Limits Mem: {total_limits_memory} Memory")

    used_requests_cpu = quota["status"]["used"].get("requests.cpu")
    used_requests_memory = quota["status"]["used"].get("requests.memory")
    used_limits_cpu = quota["status"]["used"].get("limits.cpu")
    used_limits_memory = quota["status"]["used"].get("limits.memory")

    logger.info(f"USED Resource quota:")
    logger.info(f"Used Requests CPU: {used_requests_cpu} CPU")
    logger.info(f"Used Requests Mem: {used_requests_memory} Memory")
    logger.info(f"Used Limits CPU: {used_limits_cpu} CPU")
    logger.info(f"Used Limits Mem: {used_limits_memory} Memory")


def calculate_deployment_resources(namespace, gateway_id):
    
    ingress_deployment = gateway_id
    egress_deployment = gateway_id.replace("ig", "eg")
    for deployment in [ingress_deployment, egress_deployment]:
        if check_deployment(namespace, deployment):
            # Get the deployment's resource requests and limits.
            output = subprocess.run(
                ["oc", "get", "deployment", deployment, "-n", namespace, "-o", "yaml"],
                capture_output=True,
                text=True,
            )
            deployment_yaml = yaml.safe_load(output.stdout)

            if (
                not deployment_yaml
                or "spec" not in deployment_yaml
                or "template" not in deployment_yaml["spec"]
            ):
                logger.error(f"Deployment {deployment} does not have valid spec.")
                sys.exit(1)

            containers = deployment_yaml["spec"]["template"]["spec"].get("containers", [])

            total_requests_cpu = 0
            total_limits_cpu = 0
            total_requests_memory = 0
            total_limits_memory = 0

            for container in containers:
                resources = container.get("resources", {})
                requests = resources.get("requests", {})
                limits = resources.get("limits", {})
                replicas = deployment_yaml["spec"].get("replicas", 1)

                total_requests_cpu += int(requests.get("cpu", 0).replace("m", ""))
                total_limits_cpu += int(limits.get("cpu", 0).replace("m", ""))
                total_requests_memory += int(
                    requests.get("memory", "0Mi").replace("Mi", "")
                )
                total_limits_memory += int(
                    limits.get("memory", "0Mi").replace("Mi", "")
                )

            logger.info(
                f"Deployment {deployment} in namespace {namespace} has {replicas} replicas requires:"
            )
            logger.info(
                f"Requests: {total_requests_cpu * replicas}m CPU, {total_requests_memory * replicas}Mi Memory"
            )
            logger.info(
                f"Limits: {total_limits_cpu * replicas}m CPU, {total_limits_memory * replicas}Mi Memory"
            )


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
                    # Calculate deployment compute resources
                    calculate_deployment_resources(namespace, gateway_id)
                    # Calculate namespace compute resources
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