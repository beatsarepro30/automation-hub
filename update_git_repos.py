import os
import subprocess
from datetime import datetime

# 🔧 Change this to the root directory where all your repos may be located
REPO_ROOT = r"C:\Users\YourUsername\Projects"
LOG_FILE = os.path.join(REPO_ROOT, "git_update_log.txt")

def is_git_repo(path):
    """Check if a directory is a Git repository."""
    return os.path.isdir(os.path.join(path, ".git"))

def update_repo(repo_path):
    """Run 'git pull' in the given repo path and return the output."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "pull"],
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"⚠️ Failed to update {repo_path}: {str(e)}"

def find_git_repos(root_path):
    """Recursively find all Git repos under a given root directory."""
    git_repos = set()
    for dirpath, dirnames, _ in os.walk(root_path):
        if is_git_repo(dirpath):
            git_repos.add(dirpath)
            # Prevent walking into this repo's subfolders (optimization)
            dirnames.clear()
    return sorted(git_repos)

def log_message(message):
    """Append a message to the log file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def main():
    log_message(f"\n=== Git Update Run: {datetime.now()} ===")
    repos = find_git_repos(REPO_ROOT)

    if not repos:
        log_message("❌ No Git repositories found.")
        return

    for repo in repos:
        log_message(f"\n🔄 Updating repo: {repo}")
        output = update_repo(repo)
        log_message(output.strip())

if __name__ == "__main__":
    main()
