"""Commit + push helper used inside GitHub Actions (parallel year-jobs push safely via rebase + retry)."""
import random
import subprocess
import time

from .config import ROOT


def _git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, check=check, text=True, capture_output=True)


def commit_and_push(message: str) -> None:
    _git("add", "data", "state")
    if _git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    _git("commit", "-m", message)
    for attempt in range(8):
        r = _git("pull", "--rebase", "--autostash", check=False)
        if r.returncode == 0:
            p = _git("push", check=False)
            if p.returncode == 0:
                print(f"[git] pushed: {message}", flush=True)
                return
        time.sleep(random.uniform(3, 10) * (attempt + 1))
    raise RuntimeError("git push failed after retries")
