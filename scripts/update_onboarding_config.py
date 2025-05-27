#!/usr/bin/env python3
"""
Filename      : update_onboarding_config.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
"""

import logging as log
import os
import subprocess
import sys
import pathlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

logger = log.getLogger("")
logger.setLevel(log.DEBUG)
sh = log.StreamHandler(sys.stdout)
formatter = log.Formatter(
    "[%(asctime)s] %(levelname)s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
sh.setFormatter(formatter)
logger.addHandler(sh)


def update_config_file(cluster_val_loaded):

    with open("cluster_values.yaml", "w") as igw_file:
        yaml.dump(cluster_val_loaded, igw_file)

    log.info("Cluster values config file is updated.. !")


def check_input_files():
    try:
        # Attempt to open the file
        with open("input_namespace.yaml", "r") as file:
            log.info("The required files exist.")
    except FileNotFoundError:
        log.error("Required input files dont exist. Exiting.. !")
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
    main()
