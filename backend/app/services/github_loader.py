from pathlib import Path

from git import Repo


REPO_DIR = Path("repositories")
REPO_DIR.mkdir(exist_ok=True)


def clone_repository(repo_url: str) -> Path:
    """
    Clone a repository only if it does not already exist.
    """

    repo_name = repo_url.rstrip("/").split("/")[-1]

    destination = REPO_DIR / repo_name

    if destination.exists():
        return destination

    Repo.clone_from(
        repo_url,
        destination,
    )

    return destination