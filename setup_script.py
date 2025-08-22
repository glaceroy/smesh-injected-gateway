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
from datetime import datetime

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

    script_list = [
        "1.take_quota_backup.py",
        "2.increase_quotas.py",
        "3.extract_namespaces.py",
        "4.enable_injected_gateway.py",
        "5.check_service_endpoints.py",
        "6.remove_service_labels.py",
        "7.scale_down_smcp_gateway.py",
        "8.disable_smcp_gateway.py",
        "9.update_cluster_values.py",
        "10.revert_back_quotas.py",
    ]

    log.info("")
    for script in script_list:
        script_source = "./scripts"
        if not os.path.isdir(script_source):
            log.error(f"Script source directory {script_source} does not exist.")
            sys.exit(1)  # Exit with error status
        script_fullpath = os.path.join(script_source, script)
        if not os.path.isfile(script_fullpath):
            log.error(f"Script {script} does not exist in {script_source}.")
            sys.exit(1)
        log.info(f"[ Copying Script ].......... {script}")
        shutil.copy(script_fullpath, cluster_prefix)

    return True


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
            log.info(f"Directory {dirpath} already exists")
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