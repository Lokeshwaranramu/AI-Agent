"""
GitHub automation tools for APEX AI Agent.

Requires GITHUB_TOKEN (personal access token with 'repo' + 'workflow' scopes)
and optionally GITHUB_USERNAME in .env / Streamlit secrets.

Capabilities:
  - Create public or private repositories
  - Push multiple files in a single commit
  - Create / update individual files
  - Enable GitHub Pages (gh-pages branch or /docs folder)
  - Create GitHub Actions workflows
  - List, search, and get info on repos
  - Create releases and tags
  - Create branches
  - Read existing file contents
"""

from __future__ import annotations

import base64
import os
import time
from typing import Optional

from utils.logger import log


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _get_secret(key: str) -> str:
    val = os.getenv(key, "").strip().strip('"').strip("'")
    if val:
        return val
    try:
        import streamlit as st  # type: ignore
        val = str(st.secrets.get(key, "")).strip().strip('"').strip("'")
    except Exception:
        pass
    return val


def _get_github() -> tuple:
    """
    Return (Github instance, authenticated user) or raise RuntimeError if not configured.
    """
    token = _get_secret("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. "
            "Create a Personal Access Token at https://github.com/settings/tokens "
            "with 'repo' + 'workflow' scopes, then add it to your .env / Streamlit secrets."
        )
    try:
        from github import Github, GithubException  # type: ignore
        g = Github(token)
        user = g.get_user()
        return g, user
    except ImportError:
        raise RuntimeError("PyGithub not installed. Run: pip install PyGithub")


# ─────────────────────────────────────────────
# CREATE REPOSITORY
# ─────────────────────────────────────────────

def create_repository(
    name: str,
    description: str = "",
    private: bool = True,
    auto_init: bool = True,
    gitignore_template: Optional[str] = None,
    license_template: Optional[str] = None,
    homepage: str = "",
) -> dict:
    """
    Create a new GitHub repository under the authenticated user's account.

    Args:
        name: Repository name (e.g. 'my-web-app').
        description: Short repo description.
        private: True = private repo, False = public.
        auto_init: Initialize with an empty README.
        gitignore_template: e.g. 'Python', 'Node', 'VisualStudio'.
        license_template: e.g. 'mit', 'apache-2.0'.
        homepage: Optional website URL to set on the repo.

    Returns:
        Dict with: name, full_name, html_url, clone_url, ssh_url, private.
    """
    g, user = _get_github()
    from github import GithubException  # type: ignore

    kwargs: dict = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
    }
    if gitignore_template:
        kwargs["gitignore_template"] = gitignore_template
    if license_template:
        kwargs["license_template"] = license_template
    if homepage:
        kwargs["homepage"] = homepage

    try:
        repo = user.create_repo(**kwargs)
        log.success(f"Created GitHub repo: {repo.full_name} ({'private' if private else 'public'})")
        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "private": repo.private,
            "default_branch": repo.default_branch,
        }
    except GithubException as exc:
        if exc.status == 422:
            raise RuntimeError(f"Repository '{name}' already exists or name is invalid.") from exc
        raise RuntimeError(f"GitHub API error: {exc.data}") from exc


# ─────────────────────────────────────────────
# PUSH MULTIPLE FILES
# ─────────────────────────────────────────────

def push_files(
    repo_name: str,
    files: dict[str, str],
    commit_message: str = "feat: add files via APEX AI Agent",
    branch: str = "main",
    create_branch: bool = False,
) -> dict:
    """
    Push (create or update) multiple files to a GitHub repository in one operation.

    Args:
        repo_name: Repository name (just the short name, not 'user/repo').
                   Can also be the full 'username/repo' format.
        files: Dict mapping file paths to their text content.
               e.g. {"index.html": "<html>...</html>", "style.css": "body { ... }"}
        commit_message: Git commit message.
        branch: Target branch (default 'main').
        create_branch: If True and branch doesn't exist, create it from the default branch.

    Returns:
        Dict with: repo_url, branch, files_pushed, commit_sha.
    """
    g, user = _get_github()

    # Accept both 'name' and 'owner/name'
    if "/" in repo_name:
        repo = g.get_repo(repo_name)
    else:
        repo = user.get_repo(repo_name)

    # Ensure branch exists
    if create_branch:
        try:
            repo.get_branch(branch)
        except Exception:
            source_branch = repo.default_branch
            source_sha = repo.get_branch(source_branch).commit.sha
            repo.create_git_ref(ref=f"refs/heads/{branch}", sha=source_sha)
            log.info(f"Created branch '{branch}' from '{source_branch}'")

    pushed: list[str] = []
    for file_path, content in files.items():
        try:
            existing = repo.get_contents(file_path, ref=branch)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing.sha,
                branch=branch,
            )
            log.debug(f"Updated: {file_path}")
        except Exception:
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch,
            )
            log.debug(f"Created: {file_path}")
        pushed.append(file_path)

    # Grab latest commit SHA
    try:
        commit_sha = repo.get_branch(branch).commit.sha[:7]
    except Exception:
        commit_sha = "unknown"

    log.success(f"Pushed {len(pushed)} files to {repo.full_name}@{branch}")
    return {
        "repo_url": repo.html_url,
        "branch": branch,
        "files_pushed": pushed,
        "commit_sha": commit_sha,
    }


# ─────────────────────────────────────────────
# ENABLE GITHUB PAGES
# ─────────────────────────────────────────────

def enable_github_pages(
    repo_name: str,
    branch: str = "main",
    path: str = "/",
) -> dict:
    """
    Enable GitHub Pages on a repository.

    Note: GitHub Pages on private repos requires GitHub Pro/Team.
          For free accounts, the repo must be public.
          This function will first attempt to make the repo public if needed.

    Args:
        repo_name: Repository name.
        branch: Branch to publish from (default 'main').
        path: Folder to publish from — "/" (root) or "/docs".

    Returns:
        Dict with: pages_url, status, branch, path.
    """
    token = _get_secret("GITHUB_TOKEN")
    g, user = _get_github()

    if "/" in repo_name:
        repo = g.get_repo(repo_name)
    else:
        repo = user.get_repo(repo_name)

    # GitHub Pages REST API (not fully supported by PyGithub, use raw requests)
    import requests  # type: ignore

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    pages_url = f"https://api.github.com/repos/{repo.full_name}/pages"

    # Try enabling Pages
    payload = {"source": {"branch": branch, "path": path}}
    resp = requests.post(pages_url, json=payload, headers=headers, timeout=15)

    if resp.status_code in (201, 200):
        data = resp.json()
        site_url = data.get("html_url", f"https://{user.login}.github.io/{repo.name}/")
        log.success(f"GitHub Pages enabled: {site_url}")
        return {"pages_url": site_url, "status": "enabled", "branch": branch, "path": path}

    if resp.status_code == 409:
        # Already enabled — get current Pages info
        r2 = requests.get(pages_url, headers=headers, timeout=15)
        if r2.ok:
            site_url = r2.json().get("html_url", "")
            return {"pages_url": site_url, "status": "already_enabled", "branch": branch, "path": path}

    # Possibly private repo on free plan — surface a helpful message
    error_msg = resp.json().get("message", resp.text)
    if "private" in error_msg.lower() or repo.private:
        # Attempt to make it public, then retry
        repo.edit(private=False)
        log.info("Made repo public to enable GitHub Pages (free GitHub plan)")
        resp2 = requests.post(pages_url, json=payload, headers=headers, timeout=15)
        if resp2.status_code in (201, 200):
            data = resp2.json()
            site_url = data.get("html_url", f"https://{user.login}.github.io/{repo.name}/")
            return {
                "pages_url": site_url,
                "status": "enabled (repo made public)",
                "branch": branch,
                "path": path,
            }

    raise RuntimeError(f"Failed to enable GitHub Pages: {error_msg}")


# ─────────────────────────────────────────────
# CREATE GITHUB ACTIONS WORKFLOW
# ─────────────────────────────────────────────

def create_workflow(
    repo_name: str,
    workflow_name: str,
    workflow_yaml: str,
    branch: str = "main",
) -> str:
    """
    Create a GitHub Actions workflow file.

    Args:
        repo_name: Repository name.
        workflow_name: Filename for the workflow (e.g. 'deploy.yml').
        workflow_yaml: Full YAML content of the workflow.
        branch: Target branch.

    Returns:
        URL to the created workflow file.
    """
    result = push_files(
        repo_name=repo_name,
        files={f".github/workflows/{workflow_name}": workflow_yaml},
        commit_message=f"ci: add {workflow_name} workflow",
        branch=branch,
    )
    return f"{result['repo_url']}/actions"


# ─────────────────────────────────────────────
# GET REPOSITORY INFO
# ─────────────────────────────────────────────

def get_repository(repo_name: str) -> dict:
    """
    Get information about a GitHub repository.

    Args:
        repo_name: Repository name (short or 'owner/repo').

    Returns:
        Dict with full repository details.
    """
    g, user = _get_github()
    if "/" in repo_name:
        repo = g.get_repo(repo_name)
    else:
        repo = user.get_repo(repo_name)

    pages_url = ""
    try:
        import requests
        token = _get_secret("GITHUB_TOKEN")
        r = requests.get(
            f"https://api.github.com/repos/{repo.full_name}/pages",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if r.ok:
            pages_url = r.json().get("html_url", "")
    except Exception:
        pass

    return {
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "html_url": repo.html_url,
        "clone_url": repo.clone_url,
        "private": repo.private,
        "default_branch": repo.default_branch,
        "stars": repo.stargazers_count,
        "forks": repo.forks_count,
        "pages_url": pages_url,
        "topics": repo.get_topics(),
        "created_at": str(repo.created_at),
        "updated_at": str(repo.updated_at),
    }


# ─────────────────────────────────────────────
# LIST REPOSITORIES
# ─────────────────────────────────────────────

def list_repositories(limit: int = 20) -> list[dict]:
    """
    List the authenticated user's repositories.

    Args:
        limit: Max repos to return.

    Returns:
        List of dicts with: name, full_name, private, html_url, description.
    """
    g, user = _get_github()
    repos = []
    for repo in user.get_repos(sort="updated")[:limit]:
        repos.append(
            {
                "name": repo.name,
                "full_name": repo.full_name,
                "private": repo.private,
                "html_url": repo.html_url,
                "description": repo.description or "",
                "updated_at": str(repo.updated_at),
            }
        )
    log.info(f"Listed {len(repos)} repositories")
    return repos


# ─────────────────────────────────────────────
# READ FILE FROM REPO
# ─────────────────────────────────────────────

def read_file_from_repo(repo_name: str, file_path: str, branch: str = "main") -> str:
    """
    Read the text content of a file from a GitHub repository.

    Args:
        repo_name: Repository name.
        file_path: Path to the file in the repo.
        branch: Branch to read from.

    Returns:
        Decoded text content of the file.
    """
    g, user = _get_github()
    if "/" in repo_name:
        repo = g.get_repo(repo_name)
    else:
        repo = user.get_repo(repo_name)

    content_file = repo.get_contents(file_path, ref=branch)
    return base64.b64decode(content_file.content).decode("utf-8", errors="replace")


# ─────────────────────────────────────────────
# CREATE RELEASE
# ─────────────────────────────────────────────

def create_release(
    repo_name: str,
    tag: str,
    title: str,
    body: str = "",
    prerelease: bool = False,
) -> dict:
    """
    Create a GitHub release.

    Args:
        repo_name: Repository name.
        tag: Tag name (e.g. 'v1.0.0').
        title: Release title.
        body: Release notes (Markdown).
        prerelease: Mark as pre-release.

    Returns:
        Dict with: tag, html_url, upload_url.
    """
    g, user = _get_github()
    if "/" in repo_name:
        repo = g.get_repo(repo_name)
    else:
        repo = user.get_repo(repo_name)

    release = repo.create_git_release(
        tag=tag,
        name=title,
        message=body,
        prerelease=prerelease,
        draft=False,
    )
    log.success(f"Created release {tag} for {repo.full_name}")
    return {"tag": tag, "html_url": release.html_url, "upload_url": release.upload_url}


# ─────────────────────────────────────────────
# GET AUTHENTICATED USER INFO
# ─────────────────────────────────────────────

def get_github_user() -> dict:
    """Return basic info about the authenticated GitHub user."""
    _, user = _get_github()
    return {
        "login": user.login,
        "name": user.name,
        "email": user.email,
        "public_repos": user.public_repos,
        "followers": user.followers,
        "html_url": user.html_url,
        "avatar_url": user.avatar_url,
    }
