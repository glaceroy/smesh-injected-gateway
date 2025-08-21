#!/usr/bin/env python3
"""
Filename      : update_quotas.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will revert the resource quota memory and CPU to their original values from the backup taken earlier for the smesh namespaces.
"""

import argparse
import logging
import operator
import subprocess
import sys
import types
from datetime import datetime
import os

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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_update_quotas.log",
        mode="w",
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)8s : %(message)s", datefmt="%a, %d %b %Y %H:%M:%S"
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


def revert_back_original(namespace, quota_resource, value):

    quota_name = f"{namespace}-quota"

    # Revert the resource quotas for the given namespace.
    logger.info(f"Reverting back original quota for {namespace}...")

    command = [
        "oc",
        "patch",
        "resourcequota",
        quota_name,
        "-n",
        namespace,
        "--type=merge",
        "-p",
        f'{{"spec": {{"hard": {{"{quota_resource}": "{value}"}}}}}}',
    ]

    if dry_run:
        logger.info(f"DRY RUN: Would execute: {' '.join(command)}")
    else:
        output = subprocess.run(command, capture_output=True, text=True)
        if output.returncode != 0:
            logger.error(f"Failed to revert quota for {namespace}: {output.stderr}")
            sys.exit(1)
        else:
            logger.info(f"Successfully reverted quota for {namespace}.")


def check_quota_backup_files(namespace):

    # Specify the file path
    filepath = "./backups/"
    filename = f"{namespace}_quota_backup.yaml"
    fullname = os.path.join(filepath, filename)

    # Check if the file exists
    if not os.path.exists(fullname):
        logger.error(f"Backup file {fullname} does not exist.")
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
            # Calculate the current resource quotas for the namespace
            if check_quota_backup_files(members):
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

    parser = argparse.ArgumentParser("update_quotas")
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

    args = parser.parse_args()
    dry_run = args.dry_run

    if dry_run:
        logger.info("Running in DRY RUN MODE. No changes will be made.")

    main()