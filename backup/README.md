# Backup Sync Script

A robust Bash script to **synchronize files from a source directory to a timestamped backup directory**. It supports incremental backups, preserves file permissions and symlinks, skips Git repositories, removes stale files and empty directories, manages logs, rotates old backups, and prevents overlapping runs—ideal for automated scheduled execution via cron.

---

## Features

* **Automatic configuration**: Prompts for source and destination directories on first run. Supports **absolute paths, relative paths, and `~` expansion**.
* **Command-line path overrides**: You can specify source and destination directories as script arguments, e.g.,

  ```bash
  ./backup_sync.sh ~/myproject /mnt/backups
  ```
* **Lockfile protection**: Prevents multiple instances from running simultaneously (`/tmp/sync.lock`).
* **Incremental backups**: Only copies files that are new or changed since the last backup, saving time and I/O.
* **Symlink, permissions, and timestamp preservation**: Maintains original file metadata using `cp -a`.
* **Timestamped backups**: Creates daily backup directories (`backup_YYYY-MM-DD`).
* **Backup rotation**: Keeps the most recent `MAX_BACKUPS` backups (default: 3), deleting older ones.
* **Stale file and empty directory cleanup**: Removes files no longer in the source and cleans up empty directories recursively.
* **Git repository exclusion**: Skips any directory containing a `.git` folder, including nested repositories, silently reducing log clutter.
* **Logging with automatic size management**: Logs all operations to `sync.log`, automatically truncating files larger than `MAX_LOG_SIZE` (default: 5 MB).

---

## Requirements

* Bash (version 4+ recommended)
* Standard Unix utilities: `mkdir`, `cp`, `find`, `stat`, `tail`, `rm`, `realpath`
* Writable destination directory
* Cron (optional, for scheduled execution)

---

## Installation

1. Copy the script to a desired location, e.g., `/usr/local/bin/backup_sync.sh`:

   ```bash
   sudo cp backup_sync.sh /usr/local/bin/backup_sync.sh
   sudo chmod +x /usr/local/bin/backup_sync.sh
   ```

2. Ensure the script has execute permissions:

   ```bash
   chmod +x /usr/local/bin/backup_sync.sh
   ```

---

## Configuration

On first run, the script will prompt for:

* **Source directory**: Directory to back up
* **Backup destination**: Directory where backups will be stored

This configuration is saved in `config.sh` in the same directory as the script:

```bash
SYNC_SRC="/path/to/source"
SYNC_DEST="/path/to/destination"
```

Subsequent runs automatically use this configuration unless overridden by command-line arguments.

---

## Usage

Run manually:

```bash
/path/to/backup_sync.sh
```

Optional override with custom paths:

```bash
/path/to/backup_sync.sh ~/myproject /mnt/backups
```

The script will:

1. Create a new backup (incremental).
2. Skip Git repositories.
3. Remove stale files and empty directories.
4. Rotate old backups.
5. Log all operations.

---

## Logging

* Logs are stored in the destination directory as `sync.log`.
* Maximum log size is configurable via `MAX_LOG_SIZE` (default: 5 MB). Logs exceeding this are truncated to 50% of the max size.
* Git repositories are skipped silently, reducing log verbosity.

---

## Cron Job Setup

To schedule daily backups at 2:00 AM, add a cron entry:

```bash
0 2 * * * /path/to/backup_sync.sh
```

Check cron logs if necessary:

```bash
grep CRON /var/log/syslog
```

---

## Configurable Variables

* `MAX_BACKUPS`: Number of backups to keep (default: 3)
* `MAX_LOG_SIZE`: Maximum log file size in bytes (default: 5 MB)

---

## Notes

* Entire Git repositories in the source are ignored during copy (any directory containing a `.git` folder is skipped).
* Prevents overlapping runs using a lockfile (`/tmp/sync.lock`).
* Incremental backup ensures only changed or new files are copied.
* All copied files retain original permissions, timestamps, and symlinks.
* Empty directories in the backup are automatically removed.

---

## Example Directory Structure

After running the script:

```
backup_destination/
├── backup_2025-09-22/
│   ├── file1.txt
│   ├── dir1/
│   │   └── file2.txt
├── backup_2025-09-21/
├── backup_2025-09-20/
└── sync.log
```
