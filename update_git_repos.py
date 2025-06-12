import os
import subprocess
from datetime import datetime

# 🔧 Set your root directory containing Git repositories
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
            dirnames.clear()  # Stop walking into Git repo subfolders
    return sorted(git_repos)

def ensure_log_file_exists():
    """Ensure the log file and its directory exist."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")

def prepend_to_log(new_log):
    """Prepend new_log (string) to the beginning of the log file."""
    ensure_log_file_exists()
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = ""

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(new_log + "\n" + old_content)

def main():
    log_lines = [f"=== Git Update Run: {datetime.now()} ==="]

    repos = find_git_repos(REPO_ROOT)
    if not repos:
        log_lines.append("❌ No Git repositories found.")
    else:
        for repo in repos:
            log_lines.append(f"\n🔄 Updating repo: {repo}")
            output = update_repo(repo).strip()
            log_lines.append(output)

    # Combine the new log section and prepend to the file
    full_log_block = "\n".join(log_lines) + "\n"
    prepend_to_log(full_log_block)

if __name__ == "__main__":
    main()
