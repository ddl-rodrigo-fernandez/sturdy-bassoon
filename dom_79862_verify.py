#!/usr/bin/env python3
"""
Verification script for DOM-79862.

Run this from a Domino workspace terminal, on a git-based project (GBP) whose
main repository is an external git remote (e.g. github.com/domino-field/git-commit-id-issue).

It exercises three job_start call patterns and reports what happened:

  1. commit_id=<main repo HEAD sha>
     - The bug from the ticket. On an UNPATCHED backend: job_start succeeds
       (returns a job id), but the job pod fails during setup with
       "Commit <sha> not found in git repository /mnt/artifacts/.domino/repo".
     - On the PATCHED backend: job_start itself fails immediately with a 400
       and a clear message pointing at main_repo_git_ref.

  2. main_repo_git_ref={"type": "commitId", "value": <sha>}
     - The correct way to pin a commit on a git-based project's main repo.
       Should succeed on both patched and unpatched backends -- this field
       already exists and works today; this fix doesn't change it.

  3. commit_id omitted
     - Baseline / today's workaround. Should always succeed.

Usage (from a workspace terminal):
    python dom_79862_verify.py

No arguments needed -- the project (owner/name) is read from the
DOMINO_PROJECT_OWNER / DOMINO_PROJECT_NAME env vars that are always set
inside a workspace, and the API host/key are picked up automatically by
the Domino() client from DOMINO_API_HOST / DOMINO_USER_API_KEY.
"""
import os
import subprocess
import sys
import time

from domino import Domino


def get_main_repo_head_sha():
    """Read the current HEAD commit of the main git repo checked out in this workspace."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def run_case(domino, label, **job_start_kwargs):
    print(f"\n{'=' * 70}")
    print(f"CASE: {label}")
    print(f"job_start kwargs: {job_start_kwargs}")
    print("-" * 70)

    try:
        job = domino.job_start(command="echo hello from DOM-79862 verification", **job_start_kwargs)
    except Exception as e:
        print(f"RESULT: job_start() raised immediately -> {type(e).__name__}: {e}")
        return

    job_id = job["id"]
    print(f"RESULT: job_start() succeeded, job id={job_id}, number={job.get('number')}")
    print(f"        {domino._routes.host}/{domino._owner_username}/{domino._project_name}/jobs/{job_id}")
    print("Polling for completion...")

    try:
        status = domino.job_status(job_id)
        deadline = time.time() + 180
        while not status["statuses"]["isCompleted"] and time.time() < deadline:
            time.sleep(5)
            status = domino.job_status(job_id)

        exec_status = status["statuses"]["executionStatus"]
        print(f"Final execution status: {exec_status}")

        if exec_status == "Failed":
            log = domino.get_run_log(run_id=job_id, include_setup_log=True)
            print("--- run log (tail) ---")
            print(log[-3000:] if isinstance(log, str) else log)
    except Exception as e:
        print(f"Could not poll job status/logs: {type(e).__name__}: {e}")


def main():
    project = f"{os.environ['DOMINO_PROJECT_OWNER']}/{os.environ['DOMINO_PROJECT_NAME']}"
    domino = Domino(project)

    sha = get_main_repo_head_sha()
    print(f"Domino project: {domino._owner_username}/{domino._project_name}")
    print(f"Main repo HEAD sha (from `git rev-parse HEAD` in this workspace): {sha}")

    run_case(
        domino,
        "commit_id=<main repo sha>  [the DOM-79862 bug -- expect FAILURE, "
        "immediate on patched backend, pod failure on unpatched]",
        commit_id=sha,
    )

    run_case(
        domino,
        "main_repo_git_ref={type: commitId, value: sha}  [correct way to pin -- expect SUCCESS]",
        main_repo_git_ref={"type": "commitId", "value": sha},
    )

    run_case(
        domino,
        "commit_id omitted  [baseline workaround -- expect SUCCESS]",
    )


if __name__ == "__main__":
    sys.exit(main())
