from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class SimpleUser:
    login: str
    html_url: str
    avatar_url: str


@dataclass
class Issue:
    number: int
    html_url: str
    state: Literal["open", "closed"]
    title: str
    user: Optional[SimpleUser]


@dataclass
class IssueEvent:
    action: Literal[
        "opened", "edited", "deleted", "pinned",
        "unpinned", "closed", "reopened", "assigned",
        "unassigned", "labeled", "unlabeled", "locked",
        "unlocked", "transferred", "milestoned", "demilestoned",
    ]
    issue: Issue
