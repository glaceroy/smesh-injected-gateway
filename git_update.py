"""
Filename      : git_update.py
Author        : Aiyaz Khan
Maintained by : Kyndryl Engineering
Version       : 1.0
Description   : This script will update the git repository with the injected gateway charts and update.
"""

import argparse
import logging as log
import os
import shutil
import sys

from ruamel.yaml import YAML

yaml = YAML()
yaml.width = sys.maxsize  # Set width to max size to avoid line breaks in YAML output
yaml.preserve_quotes = True  # Preserve quotes in YAML output

logger = log.getLogger("")
logger.setLevel(log.DEBUG)
sh = log.StreamHandler(sys.stdout)
formatter = log.Formatter(
    "[%(asctime)s] %(levelname)8s : %(message)s",
    datefmt="%a, %d %b %Y %H:%M:%S",
)
sh.setFormatter(formatter)
logger.addHandler(sh)

def git_push(repo_path):
    
    try:
        # Git operations
        os.chdir(repo_path)
        os.system("git checkout -b feature/injected-gateway-migration")
        os.system("git add .")
        os.system('git commit -m "Updated injected gateway charts and configurations"')
        os.system("git push origin feature/injected-gateway-migration")
        log.info("Successfully raised a PR with the changes.")
    except Exception as e:  
        log.error(f"An error occurred during git operations: {e}")
        

def update_git_repository(repo_path):

    try:
        if not os.path.exists(repo_path):
            log.error(f"The specified repository path does not exist: {repo_path}")
            return

        charts_source = "./charts/service-mesh-injected-gateway"
        charts_destination = os.path.join(repo_path, "project-mesh-onboarding/charts/service-mesh-injected-gateway")
        
        shutil.copytree(charts_source, charts_destination, dirs_exist_ok=True)

        log.info("Successfully copied chart to the repository.")
    
        # Update ansible playbook
        playbook_source = "./charts/enroll-namespaces.yml"
        playbook_destination = os.path.join(repo_path, "project-mesh-onboarding/roles/charts/tasks")
        shutil.copy2(playbook_source, playbook_destination)
                
        log.info("Successfully updated the ansible playbook in the repository.")
            
        # Push changes to git
        git_push(repo_path)

    except Exception as e:
        log.error(f"An error occurred while updating the repository: {e}")


def main():
    repo_path = args.repo
    update_git_repository(repo_path)

if __name__ == "__main__":

    parser = argparse.ArgumentParser("git_update")
    parser.add_argument(
        "--repo",
        required=True,
        type=str,
        help="Specify the git repository to update.",
    )
    if len(sys.argv) != 3:
        log.error("Please provide the relevant git repo to update.")
        log.info("USAGE: python git_update.py --repo <repo_name>")
        sys.exit(1)  # Exit with error status

    args = parser.parse_args()

    main()