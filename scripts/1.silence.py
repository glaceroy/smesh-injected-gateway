"""
Filename      : silence.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will silence all alerts in openshift.
"""

import argparse
import os
import sqlite3
import requests
from urllib3.exceptions import InsecureRequestWarning
import logging
import subprocess
import sys
import types
from datetime import datetime, timedelta
import time

import json



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
        f"./logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_silence.log",
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

def delete_silence(auth_token):
    
    alert_host = get_alert_host()
    
    with sqlite3.connect('silence_id.db') as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM alert_id WHERE name = ?", ("silence_id",))
        silence_id = cursor.fetchone()
        if silence_id:
            silence_id = silence_id[0]
        else:
            logger.error("Silence ID not found in database")
            sys.exit(1)


    headers = {
        'Authorization': 'Bearer ' + auth_token,
        'Content-Type': 'application/json'
    }

    url = f"https://{alert_host}/api/v1/silence/{silence_id}"

    # Disable warnings for certificate verification
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.request("DELETE", url, headers=headers, verify=False)

    if response.status_code == 200:
        logger.info(f"Silence {silence_id} deleted successfully")

        # Drop table after deletion
        with sqlite3.connect('silence_id.db') as connection:
            cursor = connection.cursor()
            cursor.execute("DROP TABLE IF EXISTS alert_id") 
    else:
        logger.error(f"Failed to delete silence {silence_id}: {response.status_code} - {response.text}")


def set_silence(auth_token):

    silence = 12

    os.environ['TZ'] = 'UTC'
    time.tzset()

    start_time = (datetime.now()).isoformat() + "Z"
    end_time = (datetime.now() + timedelta(hours=silence)).isoformat() + "Z"

    alert_host = get_alert_host()

    headers = {
        'Authorization': 'Bearer ' + auth_token,
        'Content-Type': 'application/json'
    }

    payload_data = json.dumps({
        "matchers": [
            {
                "name": "severity",
                "value": "critical|major|warning|Critical|Info|Warning",
                "isRegex": True
            }
        ],
        "startsAt": start_time,
        "endsAt": end_time,
        "createdBy": "api",
        "comment": "Silencing alerts for the injected gateway implementation",
        "status": {
            "state": "active"
        }
    })

    url = f"https://{alert_host}/api/v1/silences"

    # Disable warnings for certificate verification
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.request("POST", url, headers=headers, data=payload_data, verify=False)

    if response.status_code == 200:
        logger.info(f"Silence alert created until {end_time}")
        logger.info(f" - Silence ID: {response.json().get('data').get('silenceId')}")
    else:
        logger.error(f"Failed to create silence: {response.status_code} - {response.text}")

    return (response.json().get('data').get('silenceId'))


def insert_silence_id_in_db(silence_id):
    
    # Insert the silence ID into the database
    with sqlite3.connect('silence_id.db') as connection:
        cursor = connection.cursor()
        insert_query = '''INSERT INTO alert_id (name, id) VALUES (?, ?)'''
        cursor.execute(insert_query, ("silence_id", silence_id))
        connection.commit()
        

def initialize_db():

    # Create a new database (or connect to an existing one)
    with sqlite3.connect('silence_id.db') as connection:
        cursor = connection.cursor()
        
        # Clear existing entries
        cursor.execute("DROP TABLE IF EXISTS alert_id")  

        # Create the 'alert_id' table
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS alert_id (
            name TEXT NOT NULL,
            id TEXT NOT NULL
        );
        '''
        
        # Execute the SQL command
        cursor.execute(create_table_query)

        # Commit the changes
        connection.commit()


def get_alert_host():

    try:
        output = subprocess.check_output(
            ["oc", "get", "route", "-n", "openshift-monitoring", "alertmanager-main", "-o", "jsonpath={.spec.host}"],
            stderr=subprocess.STDOUT,
        )
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get silence host: {e.output}")
        sys.exit(1)


def get_auth_token():

    # Get the user authentication token.
    try:
        subprocess.check_output(
            ["oc", "whoami"],
            stderr=subprocess.STDOUT,
        )
        output = subprocess.check_output(
            ["oc", "whoami", "-t"], stderr=subprocess.STDOUT
        )
        auth_token = output.decode("utf-8").strip()
        if not auth_token:
            raise subprocess.CalledProcessError(1, "oc whoami -t", b"No token found")
        return auth_token
    except subprocess.CalledProcessError:
        logger.error(
            "You are not logged in to the OpenShift cluster. Please log in and try again."
        )
        sys.exit(1)

def main():

    logger.info(
        "============================   Starting Script Execution.  ============================"
    )
    logger.newline()

    if args.action == "create":
        initialize_db()
        auth_token = get_auth_token()
        silence_id = set_silence(auth_token)
        insert_silence_id_in_db(silence_id)
        logger.info(f"Silence ID {silence_id} stored in database.")
    elif args.action == "delete":
        # Delete silence
        auth_token = get_auth_token()
        delete_silence(auth_token)

    logger.newline()
    logger.info(
        "============================   Script Execution Completed.   ============================"
    )


if __name__ == "__main__":
    # Set global logger
    logger = create_logger()
    
    parser = argparse.ArgumentParser("silence")
    parser.add_argument(
        "--action",
        choices=["create", "delete"],
        required=True,
        help="Specify the action to perform: 'create' or 'delete'.",
    )

    args = parser.parse_args()
    if not args.action:
        logger.info("USAGE: python silence.py --action <create|delete>")
        logger.error("Please provide the relevant input to run.")
        sys.exit(1)  # Exit with error status

    main()