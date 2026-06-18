"""
tools/github_tool.py — GitHub REST API wrapper.

Handles all GitHub interactions:
- Fetching open issues and PRs
- Adding labels
- Posting comments
"""

import requests
from config.settings import settings


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _base_url() -> str:
    return f"https://api.github.com/repos/{settings.GITHUB_REPO}"


def fetch_open_issues(limit: int = 10) -> list[dict]:
    """Fetch open issues (excludes PRs) from the repository."""
    url = f"{_base_url()}/issues"
    params = {"state": "open", "per_page": limit, "sort": "created", "direction": "desc"}

    response = requests.get(url, headers=_headers(), params=params)
    response.raise_for_status()

    issues = []
    for issue in response.json():
        # GitHub returns PRs in issues endpoint — filter them out
        if "pull_request" in issue:
            continue
        issues.append({
            "number": issue["number"],
            "title": issue["title"],
            "body": (issue.get("body") or "")[:500],  # Truncate long bodies
            "labels": [label["name"] for label in issue.get("labels", [])],
            "author": issue["user"]["login"],
            "created_at": issue["created_at"],
            "url": issue["html_url"],
        })

    return issues


def fetch_open_prs(limit: int = 10) -> list[dict]:
    """Fetch open pull requests from the repository."""
    url = f"{_base_url()}/pulls"
    params = {"state": "open", "per_page": limit, "sort": "created", "direction": "desc"}

    response = requests.get(url, headers=_headers(), params=params)
    response.raise_for_status()

    prs = []
    for pr in response.json():
        prs.append({
            "number": pr["number"],
            "title": pr["title"],
            "body": (pr.get("body") or "")[:500],
            "author": pr["user"]["login"],
            "base_branch": pr["base"]["ref"],
            "head_branch": pr["head"]["ref"],
            "created_at": pr["created_at"],
            "url": pr["html_url"],
            "draft": pr.get("draft", False),
        })

    return prs


def add_label_to_issue(issue_number: int, label: str) -> bool:
    """Add a label to an issue or PR."""
    # First ensure the label exists in the repo
    _ensure_label_exists(label)

    url = f"{_base_url()}/issues/{issue_number}/labels"
    response = requests.post(url, headers=_headers(), json={"labels": [label]})

    if response.status_code in (200, 201):
        print(f"  ✓ Label '{label}' added to #{issue_number}")
        return True
    else:
        print(f"  ✗ Failed to add label: {response.status_code} {response.text}")
        return False


def post_comment_on_issue(issue_number: int, comment: str) -> bool:
    """Post a comment on an issue or PR."""
    url = f"{_base_url()}/issues/{issue_number}/comments"
    body = f"🤖 **GitHub Ops Agent**\n\n{comment}"
    response = requests.post(url, headers=_headers(), json={"body": body})

    if response.status_code == 201:
        print(f"  ✓ Comment posted on #{issue_number}")
        return True
    else:
        print(f"  ✗ Failed to post comment: {response.status_code} {response.text}")
        return False


def _ensure_label_exists(label: str):
    """Create label in repo if it doesn't exist yet."""
    label_colors = {
        "bug": "d73a4a",
        "feature": "a2eeef",
        "question": "d876e3",
        "critical": "b60205",
        "needs-review": "fbca04",
        "pr-review": "0075ca",
    }

    url = f"{_base_url()}/labels"
    color = label_colors.get(label, "ededed")

    # Check if label already exists
    response = requests.get(f"{url}/{label}", headers=_headers())
    if response.status_code == 200:
        return  # Already exists

    # Create it
    requests.post(
        url,
        headers=_headers(),
        json={"name": label, "color": color},
    )
