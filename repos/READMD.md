# Repo Manager Script

This Bash script automates the management of Git repositories in a specified parent directory. It can:

* **Recursively traverse nested directories** to detect Git repositories (`.git` directories).
* **Clone missing active repositories** from a configuration file.
* **Delete commented-out repositories**.
* **Automatically add newly detected repositories** to the configuration file.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Configuration File](#configuration-file)
4. [Usage](#usage)
5. [Examples](#examples)
6. [Behavior](#behavior)
7. [Notes](#notes)

---

## Prerequisites

* Bash shell (tested with Bash 5.x)
* Git installed and configured
* Access to all remote repositories listed in the configuration file

---

## Setup

1. Clone or download this script.
2. Ensure it is executable:

```bash
chmod +x manage_repos.sh
```

3. Set your **parent directory** where all repositories should live:

```bash
PARENT_DIR="$HOME/repos"
```

or edit the variable in the script.

---

## Configuration File

The configuration file is a plain text file, e.g., `repos_config.yml`, that defines repositories to manage.

### Format

```
<relative_path> <remote_url>
```

* **relative\_path:** Path relative to `PARENT_DIR`.
* **remote\_url:** Git repository URL (SSH or HTTPS).
* Comment lines start with `#` and represent repositories to delete if found locally.
* Empty lines are ignored.

### Example

```yaml
# Active repositories
projects/team1/repoA    git@github.com:myuser/repoA.git
tools/team2/repoB       https://github.com/myuser/repoB.git

# Commented out repositories will be deleted
# legacy/old-service     git@github.com:myuser/old-service.git

# Empty lines are allowed
```

## Usage

Run the script manually from the terminal:

```bash
./manage_repos.sh
```

### Behavior

1. **Cloning Active Repos:**

   * If the repo does not exist in `$PARENT_DIR/<relative_path>`, it will be cloned.

2. **Deleting Commented Repos:**

   * If a repo is commented out in the config and exists locally, it will be deleted.

3. **Adding New Repos Automatically:**

   * Any repository discovered in `$PARENT_DIR` but not present in the config file is automatically added to the config file.

---

### Recommendation: Running via Cron

You can schedule the script to run automatically at regular intervals using `cron`. For example, to run the script **every day at 2:00 AM**:

1. Open your crontab editor:

```bash
crontab -e
```

2. Add a line like this:

```bash
0 2 * * * /bin/bash /home/username/path/to/manage_repos.sh >> /home/username/manage_repos.log 2>&1
```

* `0 2 * * *` → runs at 2:00 AM every day
* `>> /home/username/manage_repos.log 2>&1` → appends output and errors to a log file
* Make sure to replace `/home/username/path/to/manage_repos.sh` with the actual path to your script.

3. Save and exit the editor. Cron will automatically run the script according to the schedule.

## Examples

Assume `PARENT_DIR="$HOME/repos"` and the config:

```
projects/team1/repoA    git@github.com:myuser/repoA.git
tools/team2/repoB       https://github.com/myuser/repoB.git
```

* Repo `projects/team1/repoA` does not exist → cloned automatically.
* Repo `legacy/old-service` is commented out → deleted if present.

Nested paths are supported:

```
projects/team1/repoA
projects/team2/repoB
```

---

## Notes

* The script safely ignores **empty lines** or lines with only whitespace.
* Malformed lines in the config (missing relative path or remote URL) generate a warning.
* Supports `~` expansion in paths if used in configuration or `PARENT_DIR`.
* Designed for recursive nested repositories and can handle deep folder structures.

