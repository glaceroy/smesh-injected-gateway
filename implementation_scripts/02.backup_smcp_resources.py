"""
Filename      : backup_smcp_resources.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will take a backup of the resource quota, namespace, service, service account, role, and role binding
                associated with the Service Mesh Control Plane (SMCP) in an OpenShift cluster.
                The backups will be saved in the ./backups directory.
"""

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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_backup_quota_and_service.log",
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


def take_role_binding_backup():
    
    logger.newline()
    
    output = subprocess.run(
        ["oc", "get", "rolebinding", "-A", "-l", "app.kubernetes.io/managed-by=maistra-istio-operator", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    role_binding_list = yaml.safe_load(output.stdout)

    for role_binding in role_binding_list.get("items", []):
        if role_binding['metadata']['namespace'].startswith('lbg') and role_binding['roleRef']['name'].startswith(('ig', 'eg')):
            # Save the role binding data to a file
            filepath = "./backups/role_binding"
            filename = f"{role_binding['metadata']['namespace']}_{role_binding['metadata']['name']}_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(role_binding, file)

            logger.info(
                f"Role Binding backup for '{role_binding['metadata']['name']}' in namespace '{role_binding['metadata']['namespace']}' saved to '{fullname}'"
            )

    logger.newline()      
    logger.info(
        "====================================================================================="
    )
            

def take_role_backup():

    logger.newline()
    
    output = subprocess.run(
        ["oc", "get", "role", "-A", "-l", "app.kubernetes.io/managed-by=maistra-istio-operator", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    role_list = yaml.safe_load(output.stdout)

    for role in role_list.get("items", []):
        if role['metadata']['namespace'].startswith('lbg'):
            # Save the role data to a file
            filepath = "./backups/role"
            filename = f"{role['metadata']['namespace']}_{role['metadata']['name']}_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(role, file)

            logger.info(
                f"Role backup for '{role['metadata']['name']}' in namespace '{role['metadata']['namespace']}' saved to '{fullname}'"
            )
            
    logger.newline()      
    logger.info(
        "====================================================================================="
    )
    
    
def take_service_account_backup():
    
    logger.newline()
    
    output = subprocess.run(
        ["oc", "get", "sa", "-A", "-l", "app.kubernetes.io/managed-by=maistra-istio-operator", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    sa_list = yaml.safe_load(output.stdout)

    for sa in sa_list.get("items", []):
        if sa['metadata']['namespace'].startswith('lbg'):
            # Save the service account data to a file
            filepath = "./backups/service_account"
            filename = f"{sa['metadata']['namespace']}_{sa['metadata']['name']}_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(sa, file)

            logger.info(
                f"Service Account backup for '{sa['metadata']['name']}' in namespace '{sa['metadata']['namespace']}' saved to '{fullname}'"
            )
            
    logger.newline()      
    logger.info(
        "====================================================================================="
    )


def take_service_backup():
    
    logger.newline()

    output = subprocess.run(
        ["oc", "get", "svc", "-A", "-l", "app.kubernetes.io/managed-by=maistra-istio-operator", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    service_list = yaml.safe_load(output.stdout)

    for service in service_list.get("items", []):
        if service['metadata']['namespace'].startswith('lbg'):
            # Save the service data to a file
            filepath = "./backups/service"
            filename = f"{service['metadata']['namespace']}_{service['metadata']['name']}_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(service, file)

            logger.info(
                f"Service backup for '{service['metadata']['name']}' in namespace '{service['metadata']['namespace']}' saved to '{fullname}'"
            )

    logger.newline()      
    logger.info(
        "====================================================================================="
    )
    
    
def take_namespace_backup():
    
    logger.newline()
    
    output = subprocess.run(
        ["oc", "get", "namespace", "-A", "-l", "maistra.io/member-of=istio-system", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    namespace_list = yaml.safe_load(output.stdout)

    for namespace in namespace_list.get("items", []):
        if namespace['metadata']['name'].startswith('lbg'):
            # Save the namespace data to a file
            filepath = "./backups/namespace"
            filename = f"{namespace['metadata']['name']}_namespace_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(namespace, file)

            logger.info(
                f"Namespace backup for '{namespace['metadata']['name']}' saved to '{fullname}'"
            )

    logger.newline()      
    logger.info(
        "====================================================================================="
    )
        

def take_quota_backup():
    
    logger.newline()

    output = subprocess.run(
        ["oc", "get", "resourcequota", "-A", "-o", "yaml"],
        capture_output=True,
        text=True,
    )

    quota_list = yaml.safe_load(output.stdout)

    for quota in quota_list.get("items", []):
        if quota['metadata']['namespace'].startswith('lbg'):
            # Save the quota data to a file
            filepath = "./backups/quota"
            filename = f"{quota['metadata']['namespace']}_quota_backup.yaml"
            fullname = os.path.join(filepath, filename)
            with open(fullname, "w") as file:
                yaml.dump(quota, file)

            logger.info(
                f"Quota backup for '{quota['metadata']['name']}' in namespace '{quota['metadata']['namespace']}' saved to '{fullname}'"
            )

    logger.newline()      
    logger.info(
        "====================================================================================="
    )


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

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )

    take_quota_backup()
    take_namespace_backup()
    take_service_backup()
    take_service_account_backup()
    take_role_backup()
    take_role_binding_backup()
                            
    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    
    # Set global logger
    logger = create_logger()

    # Run the main function
    main()