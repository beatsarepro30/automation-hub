# Backup Sync Script

A robust Bash script to synchronize files from a source directory to a timestamped backup directory. It includes configuration setup, log management, cleanup of old backups, and prevention of overlapping runs, making it ideal for automated scheduled execution via cron.

---

## Features

* **Automatic configuration**: Prompts for source and destination directories on first run.
* **Lockfile protection**: Prevents multiple instances from running simultaneously.
* **Timestamped backups**: Creates daily backup directories (`backup_YYYY-MM-DD`).
* **Backup rotation**: Keeps the most recent 3 backups by default, deleting older ones.
* **Stale file cleanup**: Removes files in the backup that no longer exist in the source.
* **Logging with size management**: Logs all operations to `sync.log`, automatically trimming logs larger than 5 MB.
* **Excludes entire git repositories** during synchronization (any directory containing a `.git` folder is skipped, including nested repos).
* **Silent git skipping**: Git repos are skipped without generating log entries, reducing log clutter.

---

## Requirements

* Bash (version 4+ recommended)
* Standard Unix utilities: `mkdir`, `cp`, `find`, `stat`, `tail`, `rm`, `realpath`
* Writable destination directory
* Cron (if scheduled execution is desired)

---

## Installation

1. Copy the script to a desired location, e.g., `/usr/local/bin/backup_sync.sh`:

   ```bash
   sudo cp backup_sync.sh /usr/local/bin/backup_sync.sh
   sudo chmod +x /usr/local/bin/backup_sync.sh
   ```

2. Make sure the script has execute permissions:

   ```bash
   chmod +x /usr/local/bin/backup_sync.sh
   ```

---

## Configuration

On first run, the script will prompt you for:

* **Source directory**: Directory to back up
* **Backup destination**: Directory where backups will be stored

This configuration is saved in a file named `sync_config.sh` in the same directory as the script:

```bash
SYNC_SRC="/path/to/source"
SYNC_DEST="/path/to/destination"
```

Subsequent runs will automatically use this configuration.

---

## Usage

Run manually:

```bash
/path/to/backup_sync.sh
```

The script will create a new backup, clean up stale files, rotate old backups, and log all operations.

---

## Logging

* Logs are stored in the destination directory as `sync.log`.
* Maximum log size is 5 MB; if exceeded, it will be truncated to 50% of the max size.
* Git repositories are skipped silently, reducing log verbosity.

---

## Cron Job Setup

To schedule daily backups at 2:00 AM, add a cron entry:

```bash
0 2 * * * /path/to/backup_sync.sh
```

Check cron logs if necessary to verify execution:

```bash
grep CRON /var/log/syslog
```

---

## Variables You Can Customize

* `MAX_BACKUPS`: Number of backups to keep (default: 3)
* `MAX_LOG_SIZE`: Maximum log file size in bytes (default: 5 MB)

---

## Notes

* Entire git repositories in the source are ignored during copy (any directory containing a `.git` folder is skipped).
* Prevents overlapping runs using a lockfile (`/tmp/sync.lock`).
* All copied files retain original permissions and timestamps.

---

## Example Directory Structure

After running the script:

```
backup_destination/
├── backup_2025-09-20/
│   ├── file1.txt
│   ├── dir1/
│   │   └── file2.txt
├── backup_2025-09-19/
├── backup_2025-09-18/
└── sync.log
```
