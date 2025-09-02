"""
Filename      : deploy_netpols.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script reads the smmr deploys missing netpols to the member namespace.
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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_deploy_netpols.log",
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


def deploy_netpol(namespace, netpol):

    # Deploy the NetworkPolicy to the specified namespace.
    output = subprocess.run(
        ["oc", "apply", "-f", f"../networkpolicies/{netpol}.yaml", "-n", namespace],
        capture_output=True,
    )
    if output.returncode != 0:
        logger.error(f"Failed to deploy NetworkPolicy '{netpol}' to namespace: {namespace}")
    else:
        logger.info(f"Successfully deployed NetworkPolicy '{netpol}' to namespace: {namespace}")


def check_netpols_exist(namespace):
    
    netpol_status = {}
    
    netpols = ["ingress-allow-istio-system", "egress-allow-istio-system", "ingress-allow-ingress-operator"]

    # Check if the NetworkPolicies exist in the specified namespace.
    for netpol in netpols:
        output = subprocess.run(
            ["oc", "get", "networkpolicies", netpol, "-n", namespace],
            capture_output=True,
        )
        if output.returncode != 0:
            netpol_status[netpol] = False
        else:
            netpol_status[netpol] = True
    
    for netpol, status in netpol_status.items():
        logger.info(f"  - {netpol} : {'Check OK..' if status else 'Missing..'}")

    return netpol_status


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

    # Read SMMR configuration from the OpenShift cluster.
    output = subprocess.run(
        [
            "oc",
            "get",
            "smmr",
            "default",
            "-n",
            "istio-system",
            "-o",
            "yaml",
        ],
        capture_output=True,
    )
    smmr = yaml.safe_load(output.stdout)

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )
    
    members_list = smmr["spec"]["members"]
    for member in members_list:
        logger.newline()
        logger.info(f"Checking networkpolicies in namespace: {member}")
        logger.newline()

        netpol_status = check_netpols_exist(member)
        if not all(netpol_status.values()):
            for netpol, status in netpol_status.items():
                if not status:
                    logger.newline()
                    logger.info(f"Creating the missing NetworkPolicy: {netpol}")
                    deploy_netpol(member, netpol)
                    
        else:
            logger.info(f"All NetworkPolicies are present in namespace: {member}")

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
    main()