"""
utils/helpers.py
----------------
Miscellaneous utility functions used across the CLI and models.
"""

from __future__ import annotations

import re
from typing import List, Optional


# ── Validation ────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """
    Return True if *email* matches a basic RFC-5321 pattern.

    Args:
        email: Email address string to validate.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_date(date_str: str) -> bool:
    """
    Return True if *date_str* is a valid YYYY-MM-DD date.

    Args:
        date_str: Date string to validate.
    """
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ── Search helpers ────────────────────────────────────────────────────

def find_user_by_name(users: List, name: str):
    """
    Case-insensitive search for a user by name.

    Args:
        users: List of User objects.
        name : Name to search for.

    Returns:
        The first matching User, or None.
    """
    for u in users:
        if u.name.lower() == name.lower():
            return u
    return None


def find_user_by_id(users: List, user_id: str):
    """
    Search for a user by their unique ID.

    Args:
        users  : List of User objects.
        user_id: ID string to look for.

    Returns:
        The matching User, or None.
    """
    for u in users:
        if u.user_id == user_id:
            return u
    return None


def find_project_globally(users: List, identifier: str):
    """
    Search all users' projects for a project matching the given
    project_id or title (case-insensitive).

    Args:
        users     : List of User objects.
        identifier: project_id or title string.

    Returns:
        (user, project) tuple or (None, None) if not found.
    """
    for u in users:
        for p in u.projects:
            if p.project_id == identifier or p.title.lower() == identifier.lower():
                return u, p
    return None, None


def find_task_globally(users: List, identifier: str):
    """
    Search all projects' tasks for a task matching the given
    task_id or title (case-insensitive).

    Args:
        users     : List of User objects.
        identifier: task_id or title string.

    Returns:
        (project, task) tuple or (None, None) if not found.
    """
    for u in users:
        for p in u.projects:
            for t in p.tasks:
                if t.task_id == identifier or t.title.lower() == identifier.lower():
                    return p, t
    return None, None


# ── Formatting ────────────────────────────────────────────────────────

def truncate(text: str, max_len: int = 40) -> str:
    """
    Truncate *text* to *max_len* characters, adding '…' if needed.

    Args:
        text   : String to truncate.
        max_len: Maximum character length.
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"