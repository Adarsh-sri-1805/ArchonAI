"""
app/services/git_service.py
-----------------------------
GitService — responsible ONLY for Git operations.
No embedding, no parsing, no retrieval logic here.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger("archon.git")


class GitService:

    def __init__(self, clone_root: Path | None = None):
        self._clone_root = clone_root or settings.GIT_CLONE_ROOT
        self._clone_root.mkdir(parents=True, exist_ok=True)

    def _repo_name(self, repo_url: str) -> str:
        """Extract repo name from any valid Git URL."""
        name = repo_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def _destination(self, repo_url: str) -> Path:
        return self._clone_root / self._repo_name(repo_url)

    def sync(self, repo_url: str) -> Path:
        """
        Clone the repository if it does not exist locally.
        Pull the latest changes if it already exists.
        Returns the local repository path.
        """
        try:
            from git import Repo, GitCommandError  # type: ignore
        except ImportError:
            raise RuntimeError("GitPython not installed. Run: pip install GitPython")

        destination = self._destination(repo_url)

        if destination.exists():
            logger.info("Pulling latest changes for %s", destination.name)
            try:
                repo = Repo(destination)
                origin = repo.remotes.origin
                origin.pull()
                logger.info("Pull complete. HEAD: %s", repo.head.commit.hexsha[:8])
            except GitCommandError as e:
                logger.warning("Git pull failed for %s: %s — using cached clone", destination.name, e)
        else:
            logger.info("Cloning %s → %s (shallow clone depth=1)", repo_url, destination)
            Repo.clone_from(repo_url, destination, depth=1)
            logger.info("Clone complete.")

        return destination

    def get_commit_sha(self, repo_path: Path) -> str:
        """Return the current HEAD commit SHA."""
        try:
            from git import Repo  # type: ignore
            return Repo(repo_path).head.commit.hexsha
        except Exception:
            return ""
