#!/usr/bin/env python3
"""Create or update GitHub issues from the IdentityCore implementation backlog."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

BACKLOG = Path("docs/planning/implementation-backlog.md")
ROW = re.compile(
    r"^\| (?P<id>IC-\d{3}) \| (?P<priority>P[0-2]) \| (?P<kind>[^|]+?) "
    r"\| (?P<title>[^|]+?) \| (?P<acceptance>[^|]+?) \| (?P<depends>[^|]+?) \|$"
)
MILESTONE = re.compile(r"^## Milestone (?P<number>\d+) — (?P<title>.+)$")

LABELS = {
    "status:ready": "#1D76DB",
    "P0": "#B60205",
    "P1": "#D93F0B",
    "P2": "#FBCA04",
    "type:bug": "#D73A4A",
    "type:feature": "#0E8A16",
    "type:security": "#B60205",
    "type:test": "#5319E7",
    "type:docs": "#0075CA",
}


@dataclass(frozen=True)
class BacklogIssue:
    stable_id: str
    priority: str
    kind: str
    title: str
    acceptance: str
    dependencies: str
    milestone: str

    @property
    def github_title(self) -> str:
        return f"[{self.stable_id}] {self.title}"

    @property
    def marker(self) -> str:
        return f"<!-- identitycore-backlog:{self.stable_id} -->"

    @property
    def body(self) -> str:
        dependencies = self.dependencies if self.dependencies != "—" else "None."
        return "\n".join(
            [
                self.marker,
                f"## Outcome\n{self.title}",
                f"## Acceptance checks\n- {self.acceptance}",
                f"## Dependencies\n{dependencies}",
                f"## Planning metadata\n- **Priority:** {self.priority}\n- **Milestone:** {self.milestone}",
                "## Definition of done\n"
                "- [ ] Automated tests cover the change where practical.\n"
                "- [ ] Tenant/environment isolation and failure paths were reviewed.\n"
                "- [ ] Logs and errors contain no secrets, PII, documents, or biometric data.\n"
                "- [ ] Relevant API, architecture, operations, and user documentation is updated.\n"
                "- [ ] The pull request links this issue and lists verification commands.",
                "_Generated from `docs/planning/implementation-backlog.md`; edit the backlog and rerun the sync to change generated fields._",
            ]
        )

    @property
    def labels(self) -> list[str]:
        return ["status:ready", self.priority, f"type:{self.kind}"]


def parse_backlog(path: Path) -> list[BacklogIssue]:
    issues: list[BacklogIssue] = []
    milestone = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        milestone_match = MILESTONE.match(line)
        if milestone_match:
            milestone = f"Milestone {milestone_match['number']} — {milestone_match['title']}"
            continue
        row = ROW.match(line)
        if row:
            if not milestone:
                raise ValueError(f"{row['id']} appears before a milestone heading")
            issues.append(
                BacklogIssue(
                    stable_id=row["id"],
                    priority=row["priority"],
                    kind=row["kind"],
                    title=row["title"],
                    acceptance=row["acceptance"],
                    dependencies=row["depends"],
                    milestone=milestone,
                )
            )
    ids = [issue.stable_id for issue in issues]
    if not issues or len(ids) != len(set(ids)):
        raise ValueError("backlog must contain at least one issue and no duplicate IDs")
    return issues


class GitHub:
    def __init__(self, repository: str, token: str) -> None:
        self.base = f"https://api.github.com/repos/{repository}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "identitycore-backlog-sync",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def request(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            f"{self.base}{path}", data=data, headers=self.headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response) if response.length != 0 else None
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} failed ({error.code}): {detail}") from error

    def all_issues(self) -> list[dict]:
        results: list[dict] = []
        page = 1
        while True:
            batch = self.request("GET", f"/issues?state=all&per_page=100&page={page}")
            results.extend(item for item in batch if "pull_request" not in item)
            if len(batch) < 100:
                return results
            page += 1

    def ensure_labels(self) -> None:
        existing = {label["name"] for label in self.request("GET", "/labels?per_page=100")}
        for name, color in LABELS.items():
            if name not in existing:
                self.request("POST", "/labels", {"name": name, "color": color.removeprefix("#")})

    def create(self, issue: BacklogIssue) -> dict:
        return self.request(
            "POST",
            "/issues",
            {"title": issue.github_title, "body": issue.body, "labels": issue.labels},
        )

    def update(self, number: int, issue: BacklogIssue, labels: list[str]) -> dict:
        return self.request(
            "PATCH",
            f"/issues/{number}",
            {"title": issue.github_title, "body": issue.body, "labels": labels},
        )


def sync(client: GitHub, backlog: list[BacklogIssue]) -> tuple[int, int]:
    client.ensure_labels()
    existing = {
        match.group(1): item
        for item in client.all_issues()
        if (match := re.search(r"<!-- identitycore-backlog:(IC-\d{3}) -->", item.get("body") or ""))
    }
    created = updated = 0
    for issue in backlog:
        current = existing.get(issue.stable_id)
        if current is None:
            result = client.create(issue)
            created += 1
            print(f"created #{result['number']}: {issue.github_title}")
        else:
            current_labels = {label["name"] for label in current["labels"]}
            needs_update = (
                current["title"] != issue.github_title
                or current.get("body") != issue.body
                or not set(issue.labels).issubset(current_labels)
            )
            if not needs_update:
                continue
            client.update(current["number"], issue, sorted(current_labels | set(issue.labels)))
            updated += 1
            print(f"updated #{current['number']}: {issue.github_title}")
    return created, updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backlog", type=Path, default=BACKLOG)
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY"))
    parser.add_argument("--apply", action="store_true", help="write issues using GITHUB_TOKEN")
    args = parser.parse_args()
    backlog = parse_backlog(args.backlog)
    if not args.apply:
        for issue in backlog:
            print(issue.github_title)
        print(f"dry run: {len(backlog)} issues parsed; pass --apply to synchronize")
        return 0
    token = os.getenv("GITHUB_TOKEN")
    if not args.repo or not token:
        parser.error("--apply requires --repo OWNER/REPO (or GITHUB_REPOSITORY) and GITHUB_TOKEN")
    created, updated = sync(GitHub(args.repo, token), backlog)
    print(f"sync complete: {created} created, {updated} updated, {len(backlog)} total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
