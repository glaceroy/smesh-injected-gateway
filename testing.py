#!/usr/bin/env python3
"""
Filename      : check_service_endpoints.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This scripts checks the service endpoints for injected gateways pods in an OpenShift cluster.
"""

from datetime import datetime, timedelta
import os
import time


def main():

    silence = 12

    os.environ['TZ'] = 'Europe/London'
    time.tzset()

    start_time = (datetime.now() - timedelta(minutes=1)).isoformat() + "Z"
    end_time = (datetime.now() + timedelta(hours=silence)).isoformat() + "Z"
    
    print(f"Silencing alerts from {start_time} to {end_time}")
    


if __name__ == "__main__":

    # Run the main function
    main()