#!/usr/bin/env python3
"""
Filename      : update_cluster_values.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will update the cluster values config file by disabling SMCP egress and ingress for namespaces listed in the input namespace yaml file.
"""


import logging
import os
import sys
import types
from datetime import datetime
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()
yaml.width = sys.maxsize  # Set width to max size to avoid line breaks in YAML output
yaml.preserve_quotes = True  # Preserve quotes in YAML output


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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_update_cluster_values.log",
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


def update_config_file(cluster_values):

    with open(file2, "w") as igw_file:
        yaml.dump(cluster_values, igw_file)


def main():

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )
    logger.newline()

    files = [file1, file2]
    # Check if the required files exist
    for file in files:
        if os.path.isfile(file):
            logger.info(f"The required file '{file}' exists.")
        else:
            logger.error(f"Required input file '{file}' does not exist. Exiting.. !")
            sys.exit(1)

    # Read input namespace yaml file
    with open(file1, "r") as ns_stream:
        ns_list = yaml.load(ns_stream)

    # Read cluster values yaml file
    for ns in ns_list:
        with open(file2, "r") as cv_stream:
            cluster_values = yaml.load(cv_stream)

        # Check if the namespace exists in the cluster values
        if "project" not in cluster_values:
            logger.error(
                "The cluster values file does not contain 'project' key. Exiting.. !"
            )
            logger.error(
                "Check the order of input files passed to the script. Exiting.. !"
            )
            logger.info(
                "USAGE: python update_onboarding_config.py <input_namespace.yaml> <cluster_values.yaml>"
            )
            sys.exit(1)

        for ns_index, namespace in enumerate(cluster_values["project"]):
            if ns == namespace["namespace"]:
                for index, key in enumerate(namespace):
                    if key == "egress":
                        if (
                            cluster_values["project"][ns_index]["egress"]["enabled"]
                            == True
                        ):
                            cluster_values["project"][ns_index]["egress"][
                                "enabled"
                            ] = False
                    elif key == "ingress":
                        if (
                            cluster_values["project"][ns_index]["ingress"]["enabled"]
                            == True
                        ):
                            cluster_values["project"][ns_index]["ingress"][
                                "enabled"
                            ] = False

                update_config_file(cluster_values)

    logger.info("Cluster values config file is updated.. !")
    logger.newline()
    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()

    # Check if two arguments are provided (not counting the script name)
    if len(sys.argv) != 3:
        logger.info(
            "USAGE: python update_onboarding_config.py <input_namespace.yaml> <cluster_values.yaml>"
        )
        logger.error("Please provide full path for the two input values.")
        sys.exit(1)  # Exit with error status

    # Assign values
    file1 = sys.argv[1]
    file2 = sys.argv[2]

    main()