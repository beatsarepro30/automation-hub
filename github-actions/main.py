#!/usr/bin/env python3
"""
github_workflow_runner.py

Trigger and monitor a single GitHub Actions workflow using Python.

Features:
- Repo alias support via config
- Trigger only 1 workflow at a time (from config)
- Resolve workflow ID from workflow file name
- Poll until completion
- Token read from env (preferred) or config file (fallback)
"""

import os
import sys
import time
import argparse
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
import yaml

from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("gh-wf-runner")

# ----------------------
# Config class with repo alias support
# ----------------------
class Config():
    def __init__(self, repo, workflow, config_path: str = "config.yml"):
        self.config_path = config_path
        self.repo = repo
        self.workflow = workflow
        self.poll_interval_seconds = 5
        self.load()

    def load(self):
        """Load YAML config and apply alias resolution."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_content = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.error(f"Config file '{self.config_path}' not found.")
            raise

        repos_data = config_content.get("repos", {})
        if repos_data is None:
            raise ValueError("Repos key must be provided in config and cannot be null")

        # `self.repo` initially holds the repo key from args; keep it as repo_key
        repo_key = self.repo
        self.repo_data = repos_data.get(repo_key, None)
        if self.repo_data is None:
            raise ValueError(f"Repo key '{repo_key}' not found in config.repos")

        self.owner = self.repo_data.get("owner", None)
        self.repo_name = self.repo_data.get("repo", None)
        if self.owner is None or self.repo_name is None:
            raise ValueError(f"Missing owner/repo from repo {repo_key}")

        workflows = config_content.get("workflows", None)
        if workflows is None:
            raise ValueError(f"Workflows key not found in config")

        # `self.workflow` initially holds the workflow key from args
        workflow_key = self.workflow
        self.workflow = workflows.get(workflow_key, None)
        if self.workflow is None:
            raise ValueError(f"Workflow key '{workflow_key}' not found in config.workflows")

        # Tokens: prefer env, fallback to config
        self.workflow_token = os.getenv("GITHUB_TOKEN")
        if not self.workflow_token:
            self.workflow_token = config_content.get("workflow_token", None)
        if not self.workflow_token:
            raise ValueError("No workflow token found in environment variable GITHUB_TOKEN or config key workflow_token")

        self.repo_token = os.getenv("GITHUB_REPO_TOKEN")
        if not self.repo_token:
            self.repo_token = os.getenv("GITHUB_TOKEN")  # fallback to GITHUB_TOKEN for repo token if specific one not set
        if not self.repo_token:
            self.repo_token = config_content.get("repo_token", None)
        if not self.repo_token:
            raise ValueError("No repo token found in environment variables GITHUB_REPO_TOKEN or GITHUB_TOKEN, or config key repo_token")

        self.default_ref = "main"

        self.token = self.workflow_token
        if os.getenv("GITHUB_TOKEN"):
            self.token_env = "GITHUB_TOKEN"
        else:
            self.token_env = "config.workflow_token" if config_content.get("workflow_token") else None

        self.repo_token = self.repo_token
        if os.getenv("GITHUB_REPO_TOKEN"):
            self.repo_token_env = "GITHUB_REPO_TOKEN"
        elif os.getenv("GITHUB_TOKEN"):
            self.repo_token_env = "GITHUB_TOKEN"
        else:
            self.repo_token_env = "config.repo_token" if config_content.get("repo_token") else None

# ----------------------
# GitHub Actions client
# ----------------------
class GitHubActionsClient:
    API_ROOT = "https://api.github.com"

    def __init__(self, config: Config):
        self.config = config
        # workflow-scoped session
        self.workflow_session = requests.Session()
        self.workflow_session.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "gh-wf-runner"})
        if self.config.token:
            self.workflow_session.headers.update({"Authorization": f"Bearer {self.config.token}"})
            logger.info("Workflow Authorization header set from %s", self.config.token_env)
        else:
            logger.warning("No workflow token found in env/config. Some API calls may be limited.")

        # repo-scoped session
        self.repo_session = requests.Session()
        self.repo_session.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "gh-wf-runner-repo"})
        if self.config.repo_token:
            self.repo_session.headers.update({"Authorization": f"Bearer {self.config.repo_token}"})
            logger.info("Repo Authorization header set from %s", self.config.repo_token_env)
        else:
            # do not warn loudly here because repo token is optional (we can still poll for manual approval)
            logger.debug("No repo-scoped token provided; approve APIs cannot be executed programmatically.")

        # cache for environment name -> id
        self._env_name_cache: Dict[str, Optional[int]] = {}

    def get_session(self, scope: str = "workflow") -> requests.Session:
        """
        Return the appropriate session for the given scope.
        scope: "workflow" (default) or "repo". Falls back to workflow_session if repo_session has no token.
        """
        if scope == "repo":
            if self.config.repo_token:
                return self.repo_session
            # fallback to workflow session if repo token not present
            logger.debug("Falling back to workflow session for repo-scoped request (no repo token configured)")
            return self.workflow_session
        return self.workflow_session

    def get_workflow_id_by_filename(self, workflow_file: str) -> Optional[int]:
        """Given a workflow file name (e.g., ci.yml), return its numeric workflow ID."""
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/workflows"
        r = self.get_session("workflow").get(url)
        if r.status_code != 200:
            logger.error(f"Failed to list workflows: {r.status_code} {r.text}")
            return None
        workflows = r.json().get("workflows", [])
        for wf in workflows:
            if wf.get("path", "").endswith(workflow_file):
                workflow_id = wf.get("id")
                logger.info(f"Resolved workflow file '{workflow_file}' to ID {workflow_id}")
                return workflow_id
        logger.error(f"Workflow file '{workflow_file}' not found in repo {self.config.owner}/{self.config.repo_name}")
        return None

    def trigger_workflow(self, workflow_file: str, ref: str, inputs: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Trigger workflow_dispatch. Returns run_id if found."""

        # Resolve workflow ID if a filename is passed
        if not str(workflow_file).isdigit():
            workflow_file = self.get_workflow_id_by_filename(workflow_file)
            if not workflow_file:
                raise RuntimeError("Cannot resolve workflow ID from file name.")

        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/workflows/{workflow_file}/dispatches"
        payload = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs
        logger.info(f"Dispatching workflow '{workflow_file}' on {self.config.owner}/{self.config.repo_name} (ref={ref})")
        r = self.get_session("workflow").post(url, json=payload)
        if r.status_code not in (201, 204):
            logger.error(f"Failed to dispatch workflow: {r.status_code} {r.text}")
            r.raise_for_status()

        # Give GitHub a short moment to create the run before we start polling.
        logger.debug("Sleeping %ss after dispatch to allow run creation", self.config.poll_interval_seconds)
        time.sleep(self.config.poll_interval_seconds)

        # Poll for the new run to appear.
        attempt = 0
        while True:
            attempt += 1
            run = self._find_latest_run_for_workflow(workflow_file, ref)
            if run:
                run_id = run.get("id")
                logger.info(f"Found new run id: {run_id} (after {attempt} attempts)")
                return run_id
            logger.info(f"No matching run found yet (attempt {attempt}), sleeping {self.config.poll_interval_seconds}s")
            time.sleep(self.config.poll_interval_seconds)

    def _find_latest_run_for_workflow(self, workflow_file: str, ref: str) -> Optional[Dict[str, Any]]:
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/workflows/{workflow_file}/runs"
        r = self.get_session("workflow").get(url, params={"per_page": 10})
        if r.status_code != 200:
            logger.warning(f"Failed to list workflow runs: {r.status_code} {r.text}")
            return None
        runs = r.json().get("workflow_runs", [])
        # Match a run only when the branch name or the sha equals the requested ref.
        for run in runs:
            if run.get("head_branch") == ref or run.get("head_sha") == ref:
                return run
        return runs[0] if runs else None

    def get_run(self, run_id: int) -> Dict[str, Any]:
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/runs/{run_id}"
        r = self.get_session("workflow").get(url)
        r.raise_for_status()
        return r.json()

    # NEW: list jobs for a workflow run
    def list_jobs_for_run(self, run_id: int) -> list:
        """Return list of jobs for the given workflow run. Best-effort; returns [] on error."""
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/runs/{run_id}/jobs"
        r = self.get_session("workflow").get(url, params={"per_page": 100})
        if r.status_code != 200:
            logger.warning("Failed to list jobs for run %s: %s %s", run_id, r.status_code, r.text)
            return []
        return r.json().get("jobs", [])

    # NEW: list pending deployments for a workflow run (environment approvals)
    def list_pending_deployments(self, run_id: int) -> list:
        """
        Return list of pending deployments for the given workflow run.
        Use repo session if available (it may have visibility), otherwise fall back to workflow session.
        Best-effort: returns [] on error or if endpoint not available.
        """
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/runs/{run_id}/pending_deployments"
        try:
            # prefer repo session to ensure visibility/permissions, fallback inside get_session
            r = self.get_session("repo").get(url)
        except requests.RequestException as ex:
            logger.warning("Exception when listing pending deployments for run %s: %s", run_id, ex)
            return []
        if r.status_code != 200:
            logger.debug("No pending_deployments endpoint or none for run %s: %s %s", run_id, r.status_code, r.text)
            return []
        data = r.json()
        pending = data.get("pending_deployments") if isinstance(data, dict) and "pending_deployments" in data else data
        # Normalize: ensure each pending item exposes an 'environment_id' key if possible
        normalized = []
        for pd in (pending or []):
            env_id = pd.get("environment_id") or pd.get("environment", {}).get("id") if isinstance(pd, dict) else None
            item = pd.copy() if isinstance(pd, dict) else {"raw": pd}
            if env_id:
                item["environment_id"] = env_id
            normalized.append(item)
        return normalized

    # UPDATED: approve environment pending deployments for a workflow run
    def approve_run(self, run_id: int) -> bool:
        """
        Attempt to approve environment deployments for a workflow run and block until approvals are observed cleared.
        Strategy:
         - Resolve auto_approve_env_names (if any) to ids and merge with configured auto_approve_env_ids
         - Poll pending_deployments repeatedly and approve allowed ids using the repo session
         - Wait until pending_deployments cleared
        Returns True once pending_deployments are gone.
        """
        poll_secs = self.config.poll_interval_seconds
        # resolve names configured for auto-approval
        configured_names = list(self.config.workflow.get("auto_approve_env_names", []) or [])
        resolved_ids = []
        for name in configured_names:
            eid = self.get_environment_id_by_name(name)
            if eid:
                resolved_ids.append(eid)
            else:
                logger.warning("Could not resolve environment name '%s' to id; it will not be auto-approved programmatically.", name)

        # final set of allowed ids to auto-approve (derived only from names)
        auto_allowed_ids = sorted(set(resolved_ids))
        comment = self.config.workflow.get("auto_approve_comment", "Approved by automation script")

        allowed_names = self._map_ids_to_names(auto_allowed_ids)
        logger.info("Beginning approval flow for run %s; allowed auto_approve_env_names=%s", run_id, allowed_names)

        while True:
            pending = self.list_pending_deployments(run_id)
            if not pending:
                logger.info("No pending deployments for run %s: approval clear observed.", run_id)
                return True

            # collect environment ids currently pending
            pending_env_ids = []
            for pd in pending:
                if isinstance(pd, dict) and pd.get("environment_id"):
                    pending_env_ids.append(pd["environment_id"])
            pending_names = self._map_ids_to_names(pending_env_ids)
            logger.info("Run %s has %s pending_deployments (env_names=%s)", run_id, len(pending_env_ids), pending_names)

            # Determine which pending env ids are allowed for automatic approval by config (resolved)
            allowed_to_approve = [eid for eid in pending_env_ids if eid in auto_allowed_ids]
            if allowed_to_approve and self.config.repo_token:
                # Build payload exactly as required by API
                payload = {"environment_ids": allowed_to_approve, "state": "approved", "comment": comment}
                url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/actions/runs/{run_id}/pending_deployments"
                try:
                    r = self.get_session("repo").post(url, json=payload)
                except requests.RequestException as ex:
                    logger.warning("Exception when posting approval payload for run %s: %s", run_id, ex)
                    r = None
                if r is not None:
                    if r.status_code in (200, 201, 202, 204):
                        allowed_names = self._map_ids_to_names(allowed_to_approve)
                        logger.info("Approval payload posted for env_names=%s on run %s (status %s)", allowed_names, run_id, r.status_code)
                        # wait until pending_deployments cleared
                        logger.info("Waiting for pending_deployments to clear after approval...")
                        while True:
                            pending = self.list_pending_deployments(run_id)
                            if not pending:
                                logger.info("Pending deployments cleared for run %s.", run_id)
                                return True
                            remaining_envs = [pd.get("environment_id") for pd in pending if isinstance(pd, dict) and pd.get("environment_id")]
                            remaining_names = self._map_ids_to_names(remaining_envs)
                            logger.info("Still waiting for approvals to take effect for run %s (remaining_env_names=%s). Sleeping %ss", run_id, remaining_names, poll_secs)
                            time.sleep(poll_secs)
                    else:
                        logger.warning("Approval POST for run %s returned %s: %s", run_id, r.status_code, r.text)
                else:
                    logger.warning("Approval POST failed for run %s; will retry after sleep.", run_id)
                # If POST didn't clear approvals, fall through to sleep & retry
            else:
                if allowed_to_approve and not self.config.repo_token:
                    allowed_names = self._map_ids_to_names(allowed_to_approve)
                    logger.warning("Pending envs %s are allowed for auto-approve but no repo token configured; waiting for manual approval.", allowed_names)
                else:
                    logger.info("No pending envs match configured auto_approve_env_names (configured_names=%s). Waiting for manual approval if required.", configured_names)
                # Block until pending_deployments is cleared manually
                while True:
                    pending = self.list_pending_deployments(run_id)
                    if not pending:
                        logger.info("Manual approval observed for run %s.", run_id)
                        return True
                    remaining_envs = [pd.get("environment_id") for pd in pending if isinstance(pd, dict) and pd.get("environment_id")]
                    remaining_names = self._map_ids_to_names(remaining_envs)
                    logger.info("Still waiting for manual approval for run %s (remaining_env_names=%s). Sleeping %ss", run_id, remaining_names, poll_secs)
                    time.sleep(poll_secs)

            # Sleep a bit before the next outer loop iteration
            time.sleep(poll_secs)

    # NEW: resolve an environment name to its numeric id by listing repo environments
    def get_environment_id_by_name(self, name: str) -> Optional[int]:
        """
        Return environment id for the given environment name, or None if not found.
        Uses repo-scoped session where possible and caches results.
        """
        if not name:
            return None
        if name in self._env_name_cache:
            return self._env_name_cache[name]

        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/environments"
        try:
            r = self.get_session("repo").get(url, params={"per_page": 100})
        except requests.RequestException as ex:
            logger.warning("Exception listing environments for repo %s/%s: %s", self.config.owner, self.config.repo_name, ex)
            self._env_name_cache[name] = None
            return None

        if r.status_code != 200:
            logger.debug("Failed to list environments (%s): %s %s", url, r.status_code, r.text)
            self._env_name_cache[name] = None
            return None

        data = r.json()
        envs = data.get("environments") if isinstance(data, dict) and "environments" in data else data
        found_id = None
        for env in (envs or []):
            # GitHub environment objects typically expose 'name' and 'id'
            if env.get("name") == name:
                found_id = env.get("id")
                break

        if found_id is None:
            logger.warning("Environment name '%s' not found in repo %s/%s", name, self.config.owner, self.config.repo_name)
        else:
            logger.info("Resolved environment name '%s' -> id %s", name, found_id)

        self._env_name_cache[name] = found_id
        return found_id

    # NEW helper: get environment name by id (uses/updates cache)
    def get_environment_name_by_id(self, env_id: int) -> Optional[str]:
        """Return environment name for a given id, or None if not found. Populates cache when needed."""
        # Fast path: invert cache
        for name, eid in self._env_name_cache.items():
            if eid == env_id:
                return name
        # Populate cache by listing environments
        url = f"{self.API_ROOT}/repos/{self.config.owner}/{self.config.repo_name}/environments"
        try:
            r = self.get_session("repo").get(url, params={"per_page": 100})
        except requests.RequestException as ex:
            logger.debug("Exception listing environments while resolving id %s: %s", env_id, ex)
            return None
        if r.status_code != 200:
            logger.debug("Failed to list environments while resolving id %s: %s %s", env_id, r.status_code, r.text)
            return None
        data = r.json()
        envs = data.get("environments") if isinstance(data, dict) and "environments" in data else data
        for env in (envs or []):
            name = env.get("name")
            eid = env.get("id")
            if name:
                self._env_name_cache[name] = eid
        # try invert again
        for name, eid in self._env_name_cache.items():
            if eid == env_id:
                return name
        return None

    # NEW helper: map list of ids -> readable names (fallback to id str)
    def _map_ids_to_names(self, ids: list) -> list:
        """Return list of environment names for given ids (fallback to str(id) when unknown)."""
        out = []
        for i in ids:
            n = self.get_environment_name_by_id(i)
            out.append(n if n else str(i))
        return out

# ----------------------
# Runner
# ----------------------
class Runner:
    def __init__(self, client: GitHubActionsClient, config: Config):
        self.client = client
        self.config = config

    def trigger_and_wait(self) -> Dict[str, Any]:
        workflow_cfg = self.config.workflow
        workflow_file = workflow_cfg.get("file")
        ref = workflow_cfg.get("ref") or self.config.default_ref
        inputs = workflow_cfg.get("inputs", {})

        run_id = self.client.trigger_workflow(workflow_file, ref, inputs)
        if not run_id:
            run = self.client._find_latest_run_for_workflow(workflow_file, ref)
            run_id = run.get("id") if run else None
            if not run_id:
                raise RuntimeError("Unable to determine workflow run id after dispatch")

        logger.info(f"Monitoring run {run_id}...")
        attempt = 0
        approval_attempted = False  # ensure we attempt approval at most once per run
        while True:
            attempt += 1
            run = self.client.get_run(run_id)
            status = run.get("status")
            conclusion = run.get("conclusion")
            logger.info(f"Attempt {attempt}: status={status}, conclusion={conclusion}")

            # If run is completed we're done
            if status == "completed":
                logger.info(f"Run completed with conclusion: {conclusion}")
                return run

            # Check jobs for "waiting"/approval state
            try:
                jobs = self.client.list_jobs_for_run(run_id)
            except Exception:
                jobs = []

            waiting_jobs = [
                j for j in jobs
                if (j.get("status") in ("waiting", "queued")) and (j.get("conclusion") is None)
            ]

            # Also check for pending deployments (environment approvals)
            try:
                pending_deployments = self.client.list_pending_deployments(run_id)
            except Exception:
                pending_deployments = []

            if waiting_jobs or pending_deployments:
                total_waiting = len(waiting_jobs) + len(pending_deployments)
                logger.info("Detected %s waiting items for run %s (jobs=%s, pending_deployments=%s)",
                            total_waiting, run_id, len(waiting_jobs), len(pending_deployments))
                auto_approve = bool(self.config.workflow.get("auto_approve", False))
                if auto_approve and not approval_attempted:
                    logger.info("auto_approve enabled in workflow config — attempting environment approval for run %s", run_id)
                    # approve_run now blocks until approval is completed (either programmatic or manual)
                    ok = self.client.approve_run(run_id)
                    approval_attempted = True
                    if not ok:
                        logger.warning("Approval flow ended without programmatic approval; continuing to poll for completion.")
                else:
                    if not auto_approve:
                        logger.info("auto_approve not enabled; waiting for manual approval.")
                    else:
                        logger.debug("Approval already attempted for run %s; continuing to poll.", run_id)

            # Continue polling until completion
            time.sleep(self.config.poll_interval_seconds)
        # unreachable, but keep the exception to satisfy static analysis
        raise TimeoutError("Exceeded max polling attempts waiting for workflow run to complete")

# ----------------------
# CLI
# ----------------------
def build_arg_parser():
    p = argparse.ArgumentParser(description="Trigger a single GitHub Actions workflow")
    p.add_argument("--repo", "-r", required=True, help="Repo defined in config.repos (required)")
    p.add_argument("--workflow", "-w", required=True, help="Workflow defined in config.workflows (required)")
    p.add_argument("--config", "-c", default="config.yml", help="Path to YAML config file (optional)")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt and proceed immediately")
    return p

def main(argv=None):
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    # Load .env early so Config can pick up tokens from environment variables.
    try:
        load_dotenv()
        logger.debug("Loaded .env via python-dotenv")
    except Exception as ex:
        logger.warning("Failed to load .env via python-dotenv: %s", ex)
    try:
        config = Config(config_path=args.config, repo=args.repo, workflow=args.workflow)
        # Interactive confirmation step: show a brief summary and ask the user to proceed.
        if not getattr(args, "yes", False):
            # If not a TTY, avoid blocking on input
            if not sys.stdin.isatty():
                logger.error("Non-interactive session detected and --yes/-y not provided. Aborting to avoid blocking.")
                sys.exit(1)
            # Iterate through inputs and replace any null values with a prompt for user input
            if config.workflow.get("inputs"):
                for k, v in config.workflow["inputs"].items():
                    if v is None:
                        user_val = input(f"Enter value for workflow input '{k}': ")
                        config.workflow["inputs"][k] = user_val
            summary = {
                "owner": config.owner,
                "repo": config.repo_name,
                "workflow": config.workflow.get("file"),
                "ref": config.workflow.get("ref") or config.default_ref,
                "inputs": config.workflow.get("inputs", {}),
                "token_env": config.token_env,
                "repo_token_env": config.repo_token_env,
                "auto_approve": config.workflow.get("auto_approve", False),
                "auto_approve_env_names": config.workflow.get("auto_approve_env_names", []),
            }
            logger.info("About to trigger workflow with the following parameters:")
            for k, v in summary.items():
                logger.info("  %s: %s", k, v)
            resp = input("Proceed? [y/N]: ").strip().lower()
            if resp not in ("y", "yes"):
                logger.info("Aborted by user")
                sys.exit(0)
        
        client = GitHubActionsClient(config)
        runner = Runner(client, config)
        run = runner.trigger_and_wait()
        print({
            "id": run.get("id"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "html_url": run.get("html_url"),
            "logs_url": run.get("logs_url"),
        })
    except KeyboardInterrupt:
        logger.warning("Cancelled by user")
    except Exception as e:
        logger.exception("Error running workflow")
        sys.exit(1)

if __name__ == "__main__":
    main()
