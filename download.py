#!/usr/bin/env uv

import os
from huggingface_hub import HfApi, list_repo_commits
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the dataset repository ID
repo_id = "mathewhe/chatbot-arena-elo"
repo_type = "dataset" # Specify that it's a dataset repo

# Define a base directory to store the different versions
# Each version will be saved in a subdirectory named after its commit hash
base_download_dir = "./chatbot_arena_elo_versions"
os.makedirs(base_download_dir, exist_ok=True)

logging.info(f"Fetching commit history for {repo_id}...")

try:
    # Get the list of all commits for the dataset repository
    # You might need to authenticate if the repo is private or gated,
    # but for public repos, this usually works without authentication.
    # Use HfApi().login() or set HUGGING_FACE_HUB_TOKEN environment variable if needed.
    commits = list_repo_commits(repo_id, repo_type=repo_type)
    logging.info(f"Found {len(commits)} commits (versions) for {repo_id}.")

except Exception as e:
    logging.error(f"Failed to list commits for {repo_id}: {e}")
    # Consider adding authentication instructions here if it's an auth error
    exit(1)


# Iterate through each commit and download the dataset at that revision
for i, commit in enumerate(commits):
    commit_hash = commit.commit_id
    short_commit_hash = commit_hash[:8] # Use a shorter hash for directory names
    version_dir = os.path.join(base_download_dir, short_commit_hash)

    logging.info(f"--- Processing version {i+1}/{len(commits)} (Commit: {short_commit_hash}) ---")

    # Check if this version seems to be already downloaded (basic check)
    # The actual dataset cache might be elsewhere, but this prevents re-running the load_dataset command
    # if you store a marker file or if the dir exists and you choose to skip.
    # A more robust check would involve inspecting the cache structure inside version_dir if you
    # direct the cache there fully. For simplicity, we'll just attempt loading.

    try:
        logging.info(f"Attempting to load dataset at revision {commit_hash}...")
        # Use cache_dir to attempt to isolate this version's download
        # Note: datasets library manages caching complexly. This directs download attempts
        # and metadata storage, but shared blobs might still exist in the main HF cache.
        # This provides *some* separation.
        dataset_at_revision = load_dataset(
            repo_id,
            revision=commit_hash,
            cache_dir=version_dir # Directs caching for this specific load operation
        )
        logging.info(f"Successfully loaded dataset for commit {short_commit_hash}.")
        # Optional: You could add code here to process or save the dataset if needed,
        # for example, dataset_at_revision.save_to_disk(os.path.join(version_dir, "data"))
        # However, load_dataset already downloads and caches it. The cache_dir argument
        # helps organize where the download for *this specific revision* is initiated and managed.

    except Exception as e:
        # Some historical commits might be broken or have issues loading
        logging.error(f"Failed to load dataset for commit {short_commit_hash}: {e}")
        # Decide if you want to stop or continue with the next commit
        # continue

logging.info("Finished processing all historical versions.")
logging.info(f"Dataset versions are cached. Check directories starting with {base_download_dir}/<commit_hash>")
logging.info(f"Note: The actual data files might be shared across versions in the main Hugging Face cache (~/.cache/huggingface/datasets)")
