import os
import shutil
from git import Repo, GitCommandError
import logging

log = logging.getLogger(__name__)

def clone_repo(repo_url: str, dest_folder: str = "cloned_repo") -> bool:
    """Clones or replaces a git repository locally."""
    if os.path.exists(dest_folder):
        log.info(f"Removing existing directory: {dest_folder}")
        try:
            shutil.rmtree(dest_folder)
        except OSError as e:
            log.error(f"Error removing directory {dest_folder}: {e}")
            return False

    try:
        log.info(f"Cloning repo from {repo_url} into {dest_folder}...")
        Repo.clone_from(repo_url, dest_folder)
        log.info("Repo cloned successfully.")
        return True
    except GitCommandError as e:
        log.error(f"Error cloning repo: Git command failed - {e}")
        return False
    except Exception as e:
        log.error(f"An unexpected error occurred during cloning: {e}")
        return False