#!/usr/bin/env python3
"""
Filename      : injected-gateway-config-builder.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script reads the service mesh control plane config and creates ingress and egress values file for each 
                LBG project namespace which can then be used as input for the helm chart to create injected gateway config.
"""

import logging as log
import os
import subprocess
import sys
import yaml

logger = log.getLogger("")
logger.setLevel(log.DEBUG)
sh = log.StreamHandler(sys.stdout)
formatter = log.Formatter(
    "[%(asctime)s] %(levelname)8s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
sh.setFormatter(formatter)
logger.addHandler(sh)


def generate_script(namespace, gateway_id, values_file, gateway_type):

    file_path = os.path.join("./", namespace)
    release_name = "injected-gateway-" + gateway_type + "-deploy"
    script_name = release_name + ".sh"
    full_path = os.path.join(file_path, script_name)

    with open(full_path, "w") as f:
        f.write(
            "oc patch svc "
            + gateway_id
            + " -n "
            + namespace
            + " -p"
            + """ '{"metadata": {"labels": {"app.kubernetes.io/managed-by": "Helm"}}}' """
            "\n"
            "oc patch svc "
            + gateway_id
            + " -n "
            + namespace
            + " -p"
            + """ '{"metadata": {"annotations": {"meta.helm.sh/release-name": """
            '"' + release_name + '"'
            """}}}' """
            "\n"
            "oc patch svc "
            + gateway_id
            + " -n "
            + namespace
            + " -p"
            + """ '{"metadata": {"annotations": {"meta.helm.sh/release-namespace": """
            '"' + namespace + '"'
            """}}}' """
            "\n"
            "helm install "
            + release_name
            + " injected-gateway-deploy --values "
            + values_file
            + "\n"
            + "\n"
        )

    os.chmod(full_path, 0o755)


def generate_helm_files(gateway_dict):

    file_path = os.path.join("./", gateway_dict["namespace"])
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_name = gateway_dict["namespace"] + "-" + gateway_dict["gateway"] + ".yaml"

    full_path = os.path.join(file_path, file_name)

    with open(full_path, "w") as f:
        yaml.dump(gateway_dict, f)

    generate_script(
        gateway_dict["namespace"], 
        gateway_dict["id"], 
        file_name,
        gateway_dict["gateway"]
    )


def build_helm_config(smcp, gateway_id, gateway_type):

    gateway_list = smcp["spec"]["gateways"][gateway_type][gateway_id]

    if gateway_type == "additionalIngress":
        type = "ingressgateway"
    else:
        type = "egressgateway"

    gateway_dict = {}
    gateway_dict["namespace"] = gateway_list["namespace"]
    gateway_dict["id"] = gateway_id
    gateway_dict["gateway"] = type
    gateway_dict["replicaCount"] = gateway_list["runtime"]["deployment"]["replicas"]
    gateway_dict["podAnnotations"] = gateway_list["runtime"]["pod"]["metadata"]["annotations"]
    gateway_dict["resources"] = gateway_list["runtime"]["container"]["resources"]

    generate_helm_files(gateway_dict)


def check_login():

    try:
        proc = subprocess.check_output(
            ["oc", "whoami"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        log.error("Please login to the cluster and try again... !")
        sys.exit(1)

    log.info("Already logged in. Using existing login session.. !")


def main():

    check_login()

    output = subprocess.run(
        [
            "oc",
            "get",
            "smcp",
            "app-mesh-01",
            "-n",
            "istio-system",
            "-o",
            "yaml",
        ],
        capture_output=True,
    )
    smcp = yaml.safe_load(output.stdout)

    gateway_list = smcp["spec"]["gateways"]

    log.info("Generating injected gateway config files. Please wait.. !")

    for gateway_type in gateway_list:
        if gateway_type in ["additionalEgress", "additionalIngress"]:
            for gateway_id in smcp["spec"]["gateways"][gateway_type]:
                build_helm_config(smcp, gateway_id, gateway_type)

    log.info("Success...! All injected gateway config files generated")


if __name__ == "__main__":
    main()