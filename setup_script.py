#!/usr/bin/env python3
"""
Filename      : setup_script.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will create cluster prefix folders and copy relevant scripts
"""

import argparse
import os
import shutil
import sys
from datetime import datetime


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
        script = os.path.join("./scripts", script)
        if not os.path.exists(script):
            print(f"Failed: Script {script} does not exist.")
            sys.exit(1)  # Exit with error status
        print(f"Copying script {script}....")
        shutil.copy(script, cluster_prefix)
    
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
            print(f"Directory {dirpath} already exists")
        except Exception as e:
            print(f"Failed to create directory {dirpath}: {e}")
        else:
            print(f"Directory {dirpath} created")

    return True


def main():

    if create_directory(cluster_prefix):
        if copy_scripts(cluster_prefix):
            print("Setup completed successfully.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser("setup_script")
    parser.add_argument(
        "--cluster_prefix",
        required=True,
        type=str,
        help="Specify the cluster prefix for the folder name. Example rk-dt or pb-gen-preprod.",
    )
    if len(sys.argv) != 3:
        print("ERROR: Please provide the relevant input to run.")
        print("USAGE: python setup_script.py --c <cluster_prefix>")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()
    cluster_prefix = args.cluster_prefix

    main()