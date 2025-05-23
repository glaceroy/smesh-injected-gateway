#!/usr/bin/env python3
"""
Filename      : update_onboarding_config.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
"""

import os
import subprocess
import sys
import pathlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

def main():

    # Read input namespace yaml file
    with open("input_namespace.yaml", 'r') as i_stream:
        data_loaded = yaml.load(i_stream)

    for val in data_loaded:
        with open("cluster_values.yaml", 'r') as c_stream:
            cluster_val_loaded = yaml.load(c_stream)

        for ns_index, namespace in enumerate(cluster_val_loaded['project']):
            if val == namespace['namespace']:
                for index, item in enumerate(namespace):
                    if item == "egress":
                        cluster_val_loaded['project'][ns_index]['egress']['injected_egress'] = 'true'

                    elif item == "ingress":
                        cluster_val_loaded['project'][ns_index]['ingress']['injected_ingress'] = 'true'

                
                with open("cluster_values.yaml", 'w') as igw_file:
                    yaml.dump(cluster_val_loaded, igw_file)


if __name__ == "__main__":
    main()