#!/usr/bin/env python3
"""
Filename      : check_role_bindings
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This scripts checks the role bindings
"""

import subprocess


def get_role_bindings(namespace, rolebinding_name="ig002-sds"):

    # Read rolebinding 
    output = subprocess.run(
        [
            "oc","get","rolebinding",rolebinding_name,"-n",namespace,"-o","jsonpath={.roleRef[*].name}"
        ],
        capture_output=True,
    )
    smmr = output.stdout
    print(smmr)
    
def main():

    get_role_bindings(namespace="lbg-ocp-bookinfo-200-test")
    


if __name__ == "__main__":

    # Run the main function
    main()