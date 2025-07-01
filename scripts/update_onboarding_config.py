#!/usr/bin/env python3
"""
Filename      : update_onboarding_config.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
"""

import logging
import sys
from datetime import datetime
import types
import os
from pathlib import Path

from ruamel.yaml import YAML
yaml = YAML()

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



def update_config_file(cluster_val_loaded):

    with open("cluster_values.yaml", "w") as igw_file:
        yaml.dump(cluster_val_loaded, igw_file)

    logger.info("Cluster values config file is updated.. !")


def check_input_files():
    try:
        # Attempt to open the file
        with open("input_namespace.yaml", "r") as file:
            logger.info("The required files exist.")
    except FileNotFoundError:
        logger.error("Required input files dont exist. Exiting.. !")
        sys.exit(1)


def main():

    check_input_files()

    # Read input namespace yaml file
    with open("input_namespace.yaml", "r") as i_stream:
        data_loaded = yaml.load(i_stream)

    for val in data_loaded:
        with open("cluster_values.yaml", "r") as c_stream:
            cluster_val_loaded = yaml.load(c_stream)

        for ns_index, namespace in enumerate(cluster_val_loaded["project"]):
            if val == namespace["namespace"]:
                for index, item in enumerate(namespace):
                    if item == "egress":
                        cluster_val_loaded["project"][ns_index]["egress"]["injected_egress"] = "true"

                    elif item == "ingress":
                        cluster_val_loaded["project"][ns_index]["ingress"]["injected_ingress"] = "true"

                update_config_file(cluster_val_loaded)


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()
    main()