# 🧰 WSL2 Bootstrap Scripts

This directory contains a collection of **bootstrap scripts** designed to quickly set up new **WSL2 (Windows Subsystem for Linux)** instances with a baseline set of system utilities, development environments, and quality-of-life enhancements.

Each script is tailored for a particular WSL distribution and aims to automate repetitive setup tasks so that you can get a consistent environment up and running in minutes.

---

## 🚀 Purpose

The scripts provide a standardized way to:

* Update the system and install required packages
* Set up version control and development environments
* Install core command-line utilities for productivity and troubleshooting
* Optionally configure shells and other user environment enhancements

This helps reduce manual setup steps when provisioning new WSL2 instances.

---

## ⚙️ Usage

> **Run as root inside the WSL instance.**

```bash
sudo bash bootstrap-<distro>.sh
```

After the script completes, follow any post-installation instructions printed to finalize the setup.

---

## 🔧 Recommended Post-Setup

Depending on the distribution and your needs, post-setup tasks may include:

* Enabling systemd or other background services
* Restarting the WSL instance
* Verifying that key tools and services are installed correctly

---

## 🧩 Extending

To customize or extend:

* Add additional package installations or configuration steps to the relevant script
* Keep scripts modular and safe to rerun
* Test changes in a clean WSL2 instance before deploying widely
