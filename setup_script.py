"""
Filename      : setup_script.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will create cluster prefix folders and copy relevant scripts
"""

import argparse
import logging as log
import os
import shutil
import sys

logger = log.getLogger("")
logger.setLevel(log.DEBUG)
sh = log.StreamHandler(sys.stdout)
formatter = log.Formatter(
    "[%(asctime)s] %(levelname)8s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
sh.setFormatter(formatter)
logger.addHandler(sh)


def copy_scripts(cluster_prefix):


    log.info("")
    script_source = ["implementation_scripts", "pre_check_scripts", "backout_scripts"]
    for script in script_source:
        dest = os.path.join(f"./{cluster_prefix}", script)
        try:
            shutil.copytree(script, dest)
        except Exception as e:
            log.error(f"Failed to copy {script} to {dest}: {e}")
            return False
        else:
            log.info(f"Copied {script} to {dest}")


def create_directory(cluster_prefix):

    folder_list = [cluster_prefix, "logs", "backups/quota", "backups/service", "backups/namespace", "backups/service_account", "backups/role", "backups/role_binding"]
    for folder in folder_list:
        if folder is cluster_prefix:
            dirpath = os.path.join("./", folder)
        else:
            dirpath = os.path.join(f"{cluster_prefix}", folder)
        try:
            os.makedirs(dirpath, exist_ok=True)
        except Exception as e:
            log.error(f"Failed to create directory {dirpath}: {e}")
        else:
            log.info(f"Directory {dirpath} created")

    return True


def main():

    if create_directory(cluster_prefix):
        if copy_scripts(cluster_prefix):
            log.info("")
            log.info(f"All required scripts are located under ./{cluster_prefix}")
            log.info("")
            log.info("Setup completed successfully.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser("setup_script")
    parser.add_argument(
        "--cluster_prefix",
        required=True,
        type=str,
        help="Specify the cluster prefix for the folder name. Example rk-dt or pb-gen-preprod.",
    )
    if len(sys.argv) != 3:
        log.error("Please provide the relevant input to run.")
        log.info("USAGE: python setup_script.py --c <cluster_prefix>")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    cluster_prefix = args.cluster_prefix

    main()