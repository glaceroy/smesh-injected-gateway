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
import yaml

def main():

    # Read input namespace yaml file
    with open("input_namespace.yaml", 'r') as i_stream:
        data_loaded = yaml.safe_load(i_stream)

    for val in data_loaded:
        with open("cluster_values.yaml", 'r') as c_stream:
            cluster_val_loaded = yaml.safe_load(c_stream)

        for namespace in cluster_val_loaded['project']:
            if val == namespace['namespace']:
                for index, item in enumerate(namespace):
                    if item == "egress":
                        cluster_val_loaded['project'][0]['egress']['injected_egress'] = 'true'
                        #print(cluster_val_loaded)

                        #with open("cluster_values.yaml", 'w') as eg_file:
                        #    yaml.dump(cluster_val_loaded, eg_file, sort_keys=False)

                    elif item == "ingress":
                        cluster_val_loaded['project'][0]['ingress']['injected_ingress'] = 'true'

                        #with open("cluster_values.yaml", 'a') as ig_file:
                        #    yaml.dump(cluster_val_loaded, ig_file, sort_keys=False)

                with open("cluster_values.yaml", 'w') as igw_file:
                    yaml.dump(cluster_val_loaded, igw_file, sort_keys=False)


if __name__ == "__main__":
    main()