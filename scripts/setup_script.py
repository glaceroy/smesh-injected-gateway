#!/usr/bin/env python3
"""
Filename      : setup_script.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will create cluster prefix folders and copy relevant scripts
"""

import argparse
import logging
import os
import shutil
import sys
import types
from datetime import datetime


def log_newline(self, how_many_lines=1):

    # Switch formatter, output a blank line
    self.handler.setFormatter(self.blank_formatter)

    for i in range(how_many_lines):
        self.info("")

    # Switch back
    self.handler.setFormatter(self.formatter)


def create_logger(cluster_prefix):

    # Create a handler
    sh = logging.StreamHandler(sys.stdout)
    handler = logging.FileHandler(
        f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{cluster_prefix}-setup_script.log",
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


def copy_scripts(cluster_prefix):

    script_list = [
        "1.take_quota_backup.py",
        "2.update_quotas.py",
        "3.extract_namespaces.py",
        "4.enable_injected_gateway.py",
        "5.check_service_endpoints.py",
        "6.remove_service_labels.py",
        "7.scale_down_smcp_gateway.py",
        "8.disable_smcp_gateway.py",
        "9.update_cluster_values.py",
    ]

    for script in script_list:
        logger.info(f"Copying script {script}....")
        shutil.copy(script, cluster_prefix)


def create_directory(cluster_prefix):

    folder_list = [cluster_prefix, "logs", "backups"]
    for folder in folder_list:
        if folder is cluster_prefix:
            dirpath = os.path.join("./", folder)
        else:
            dirpath = os.path.join(f"{cluster_prefix}", folder)
        try:
            os.mkdir(dirpath)
        except FileExistsError:
            logger.warning(f"Directory {dirpath} already exists")
        else:
            logger.info(f"Directory {dirpath} created")


def main():

    create_directory(cluster_prefix)
    copy_scripts(cluster_prefix)


if __name__ == "__main__":

    parser = argparse.ArgumentParser("setup_script")
    parser.add_argument(
        "--cluster_prefix",
        required=True,
        type=str,
        help="Specify the cluster prefix for the folder name. Example rk-dt or pb-gen-preprod.",
    )
    if len(sys.argv) != 3:
        print("USAGE: python setup_script.py --c <cluster_prefix>")
        print("ERROR: Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    cluster_prefix = args.cluster_prefix

    # Set global logger
    logger = create_logger(cluster_prefix)

    main()