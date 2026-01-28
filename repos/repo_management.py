#!/usr/bin/env python3
import os
import subprocess
import sys
import yaml
import json
from pathlib import Path

REPOS_FILE = "repos.yml"

class RepoManager():
    def __init__(self):
        self.repos_file_path = f"{Path(__file__).resolve().parent}/{REPOS_FILE}"
        self.repos_file_content = self.load_repos_file(Path(self.repos_file_path))
        self.parent_dir = self.repos_file_content.get("parent_dir")
        pass
    
    def load_yaml(self, yaml_file: Path):
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
        with yaml_file.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def create_repos_file(self, repos_file: Path) -> dict:
        # Get user input for parent directory
        parent_dir = ""
        while not parent_dir:
            parent_dir = input("Enter parent directory where repos will be managed: ").strip()
            
            # Check if the directory exists        
            expanded_dir = os.path.expanduser(parent_dir)
            if not os.path.isdir(expanded_dir):
                print(f"Directory '{expanded_dir}' does not exist. Please enter a valid directory.")
                parent_dir = ""

        parent_dir = os.path.expanduser(parent_dir)
        repo_file_content = {"parent_dir": parent_dir, "repos": []}
        with repos_file.open("w", encoding="utf-8") as f:
            yaml.dump(repo_file_content, f)
        print(f"Configuration saved to {repos_file}")
        return repo_file_content

    def load_repos_file(self, repos_file: Path) -> str:
        if not repos_file.exists():
            repo_file_content = self.create_repos_file(repos_file)
        else:
            repo_file_content = self.load_yaml(repos_file)
        return repo_file_content

    def find_git_repos(self, root: Path):
        git_repos = []
        for dirpath, dirnames, _ in os.walk(root):
            if ".git" in dirnames:
                git_repos.append(Path(dirpath))
                dirnames[:] = [d for d in dirnames if d != ".git"]
        return git_repos

    def get_relative_path(self, path: str) -> str:
        expanded_path = os.path.expanduser(path)
        expanded_parent = os.path.expanduser(self.parent_dir)
        if expanded_path.startswith(expanded_parent + os.sep):
            return expanded_path[len(expanded_parent) + 1 :]
        raise ValueError(f"Path '{expanded_path}' is not under parent directory '{expanded_parent}'")

    def get_git_remote(self, repo_dir: Path) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_dir), "config", "--get", "remote.origin.url"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                return url if url else None
        except Exception:
            return None
        return None

    def cleanup_empty_dirs(self, root: Path) -> None:
        for dirpath, dirnames, filenames in os.walk(root, topdown=False):
            if ".git" in dirnames:
                continue
            if not dirnames and not filenames:
                try:
                    Path(dirpath).rmdir()
                except OSError:
                    pass

    def process_repos_file(self):
        git_repos = self.find_git_repos(Path(self.parent_dir))
        # Filter enabled and disabled repos from the repos file content, consider case where repos values is None
        enabled_repos = {}
        disabled_repos = {}

        if self.repos_file_content.get("repos") is not None:
            for repo_name, repo_info in self.repos_file_content.get("repos").items():
                if repo_info.get("enabled", True):
                    enabled_repos[repo_name] = repo_info
                else:
                    disabled_repos[repo_name] = repo_info

        # Add any new git repos to the repos file if not already present
        for repo_path in git_repos:
            relative_path = self.get_relative_path(str(repo_path))
            if relative_path not in list(enabled_repos.keys()) + list(disabled_repos.keys()):
                remote_url = self.get_git_remote(repo_path)
                if remote_url:
                    print(f"Adding new repo to enabled repos list: {repo_path} {remote_url}")
                    enabled_repos[relative_path] = {
                        "url": remote_url,
                        "enabled": True
                    }
                else:
                    print(f"Warning: repo {repo_path} has no remote URL, skipping addition to config")

        # Add missing enabled repos from the filesystem
        for repo_name, repo_info in enabled_repos.items():
            repo_full_path = Path(self.parent_dir) / repo_name
            if not (repo_full_path.is_dir() and (repo_full_path / ".git").is_dir()):
                remote_url = repo_info.get("url")
                if remote_url:
                    print(f"Cloning missing enabled repo: {repo_full_path} from {remote_url}")
                    repo_full_path.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(["git", "clone", remote_url, str(repo_full_path)], check=True)
                else:
                    print(f"Warning: enabled repo {repo_name} has no URL specified, cannot clone")

        # Remove any disabled repos from the filesystem
        for repo_name, repo_info in disabled_repos.items():
            repo_full_path = Path(self.parent_dir) / repo_name
            if repo_full_path.is_dir() and (repo_full_path / ".git").is_dir():
                print(f"Deleting disabled repo: {repo_full_path}")
                try:
                    subprocess.run(["rm", "-rf", str(repo_full_path)], check=True)
                except subprocess.CalledProcessError:
                    print(f"Warning: failed to delete {repo_full_path}", file=sys.stderr)
        
        # Remove empty directories under parent directory (excluding git repos)
        self.cleanup_empty_dirs(Path(self.parent_dir))

        # Combine enabled and disabled repos
        combined_repos = {}
        combined_repos.update(enabled_repos)
        combined_repos.update(disabled_repos)
        # Update the repos file content
        self.repos_file_content["repos"] = combined_repos
        # Write back to the repos file
        with Path(self.repos_file_path).open("w", encoding="utf-8") as f:
            yaml.dump(self.repos_file_content, f)

        # Create a symlink to the repos file from the parent directory
        symlink_path = Path(self.parent_dir) / REPOS_FILE
        try:
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()
            symlink_path.symlink_to(Path(self.repos_file_path).resolve())
            print(f"Created symlink to repos file at {symlink_path}")
        except Exception as e:
            print(f"Warning: failed to create symlink at {symlink_path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    manager = RepoManager()
    print(f"Using parent directory: {manager.parent_dir}")
    manager.process_repos_file()
    print("Repository management process completed.")
