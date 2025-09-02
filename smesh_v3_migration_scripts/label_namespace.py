"""
Filename      : label_namespace.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script applies smesh v3 labels to all smmr members
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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_label_namespace.log",
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


def apply_labels(namespace, labels):

    for label in labels:
        if dry_run:
            # Simulate the command output for dry run
            output = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=f"oc label namespace {namespace} --overwrite {label}",
            )
            logger.info(f"DRY RUN Command: '{output.stdout}'")
            logger.newline()
        else:
            logger.info(f"Applying label to namespace '{namespace}'")
            output = subprocess.run(
                [
                    "oc",
                    "label",
                    "namespace",
                    namespace,
                    "--overwrite",
                    label,
                ],
                capture_output=True,
                text=True,
            )
            if output.returncode != 0:
                logger.error(
                    f"Failed to apply label {label} to namespace '{namespace}': {output.stderr}"
                )
                sys.exit(1)
            else:
                logger.info(
                    f"label {label} applied to namespace '{namespace}'"
                )
            

def check_namespace_exists(namespace):

    # Check if a namespace exists.

    output = subprocess.run(
        ["oc", "get", "namespace", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.warning(f"Namespace '{namespace}' does not exist.")
        logger.newline()
        return False
    else:
        logger.info(f"Namespace '{namespace}' exists.")
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

    logger.newline()
    logger.info("Extracting namespaces from SMMR configuration...")
    members_list = smmr["spec"]["members"]
    
    labels = ["istio-discovery=enabled", "maistra.io/ignore-namespace=true"]

    for member in members_list:
        if check_namespace_exists(member):
            apply_labels(member, labels)

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
        logger.info(
            "********************************************************************"
        )
        logger.info(
            "****       Running in DRY RUN MODE. No changes will be made.    ****"
        )
        logger.info(
            "********************************************************************"
        )
        logger.newline()

    main()