"""Make a throwaway clone of a repo and export the change made in it."""

import os
import subprocess


def _git(repo, args):
    """Run git with the given words inside repo and return the finished process."""

    return subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True,
        text=True,
    )


def _git_ok(repo, args):
    """Run git with the given words inside repo, raise if it fails, and return its output text."""

    result = _git(repo, args)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {result.stderr.strip()}")
    return result.stdout


def _is_repo_top(repo_path):
    """Return True if repo_path is the top folder of a git work tree."""

    if not os.path.isdir(repo_path):
        return False
    result = _git(repo_path, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return False
    top = result.stdout.strip()
    return os.path.realpath(top) == os.path.realpath(repo_path)


def _is_commit(repo_path, base):
    """Return True if base names a commit in repo_path."""

    result = _git(repo_path, ["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"])
    return result.returncode == 0


def make_clone(repo_path, base, dest):
    """Clone repo_path into dest, check out base detached, remove origin, and return dest."""

    if not _is_repo_top(repo_path):
        raise FileNotFoundError(f"repo_path is not a git repo: {repo_path}")
    if not _is_commit(repo_path, base):
        raise ValueError(f"base is not a commit in the repo: {base}")
    if os.path.exists(dest):
        raise FileExistsError(f"dest already exists: {dest}")

    clone = subprocess.run(
        ["git", "clone", "--no-hardlinks", "--no-checkout", "-q", repo_path, dest],
        capture_output=True,
        text=True,
    )
    if clone.returncode != 0:
        raise RuntimeError(f"git clone failed for {repo_path}: {clone.stderr.strip()}")

    _git_ok(dest, ["checkout", "-q", "--detach", base])
    _git_ok(dest, ["remote", "remove", "origin"])
    return dest


def export_patch(clone_path, base):
    """Stage every change in clone_path and return the staged diff against base as text."""

    _git_ok(clone_path, ["add", "-A"])
    patch = _git_ok(clone_path, ["diff", "--cached", "--binary", base])
    if patch == "":
        raise ValueError(f"no patch exported: no change was made in {clone_path}")
    return patch
