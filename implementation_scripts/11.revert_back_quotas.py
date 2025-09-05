"""
Filename      : revert_back_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will revert the resource quota memory and CPU to their original values from the backup taken earlier for the smesh namespaces.
"""

import argparse
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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_revert_back_quotas.log",
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


def display_current_values(namespace):

    output = subprocess.run(
        [
            "oc",
            "get",
            "quota",
            f"{namespace}-quota",
            "-n",
            namespace,
            "-o",
            "yaml",
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(
            f"Failed to retrieve current resource quota for namespace '{namespace}': {output.stderr}"
        )
        return False

    logger.info(f"Current resource quota :")
    quota = yaml.safe_load(output.stdout)

    requests_cpu = quota["status"]["hard"].get("requests.cpu")
    requests_memory = quota["status"]["hard"].get("requests.memory")
    limits_cpu = quota["status"]["hard"].get("limits.cpu")
    limits_memory = quota["status"]["hard"].get("limits.memory")

    logger.info(f" - CPU Requests       : {requests_cpu} CPU")
    logger.info(f" - CPU Limits         : {limits_cpu} CPU")
    logger.info(f" - Memory Requests    : {requests_memory}")
    logger.info(f" - Memory Limits      : {limits_memory}")
    logger.newline()


def patch_namespace_quota(namespace, quota_resource, value):

    quota_name = f"{namespace}-quota"

    if dry_run:
        # Simulate the patching action without executing it
        output = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f'oc patch quota {quota_name} -n {namespace} --type=merge -p \'{{"spec": {{"hard": {{"{quota_resource}": "{value}"}}}}}}\'',
            stderr="",
        )
        # Log the dry run output
        logger.info(f"DRY RUN Command: {output.stdout}")
    else:
        # Log the action of patching the resource quota
        logger.info(
            f"Patching resource quota for namespace '{namespace}' with '{quota_resource}' = '{value}'"
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


def revert_back_original(namespace):

    # Specify the file path
    filepath = "./backups/"
    filename = f"{namespace}_quota_backup.yaml"
    fullpath = os.path.join(filepath, filename)

    if not os.path.exists(fullpath):
        logger.error(f"Backup file '{fullpath}' does not exist. OMG !!!")
        logger.newline()
        return False

    with open(fullpath, "r") as f:
        backup_data = yaml.safe_load(f)

    if not backup_data:
        logger.error(f"Failed to load backup data from '{fullpath}'.")
        return False

    requests_cpu = backup_data.get("spec", {}).get("hard", {}).get("requests.cpu", "")
    limits_cpu = backup_data.get("spec", {}).get("hard", {}).get("limits.cpu", "")
    requests_memory = (
        backup_data.get("spec", {}).get("hard", {}).get("requests.memory", "")
    )
    limits_memory = backup_data.get("spec", {}).get("hard", {}).get("limits.memory", "")

    logger.newline()
    logger.info(
        f"Reverting back to original quota values from backup file '{fullpath}':"
    )
    logger.info(f" - CPU Requests       : {requests_cpu} CPU")
    logger.info(f" - CPU Limits         : {limits_cpu} CPU")
    logger.info(f" - Memory Requests    : {requests_memory}")
    logger.info(f" - Memory Limits      : {limits_memory}")
    logger.newline()

    # Apply the changes
    patch_namespace_quota(namespace, "requests.cpu", requests_cpu)
    patch_namespace_quota(namespace, "limits.cpu", limits_cpu)
    patch_namespace_quota(namespace, "requests.memory", requests_memory)
    patch_namespace_quota(namespace, "limits.memory", limits_memory)

    if not dry_run:
        logger.info(f"Quota reverted successfully for namespace '{namespace}'.")

    logger.newline()
    display_current_values(namespace)


def check_quota(namespace):

    # Check if a quota exists for the given namespace.
    output = subprocess.run(
        [
            "oc",
            "get",
            "quota",
            f"{namespace}-quota",
            "-n",
            namespace,
            "-o",
            "yaml",
        ],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(f"Quota '{namespace}-quota' does not exist.")
        logger.newline()
        return False
    logger.info(f"Quota '{namespace}-quota' exists.")
    return True


def check_namespace(namespace):

    # Check if a namespace exists.
    output = subprocess.run(
        ["oc", "get", "namespace", namespace],
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        logger.error(f"Namespace '{namespace}' does not exist.")
        return False
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

    members_list = smmr["spec"]["members"]

    for members in members_list:
        # Check if namespace exists
        if check_namespace(members):
            # Check if quota exists in the namespace
            if check_quota(members):
                # Revert back the resource quotas for the given namespace.
                revert_back_original(members)

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

    parser = argparse.ArgumentParser("revert_back_quotas")
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
        logger.info("USAGE: python revert_back_quotas.py --dry-run (OR) --execute")
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