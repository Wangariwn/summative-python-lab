"""
utils/storage.py
----------------
JSON-based persistence layer.

All reads and writes go through this module so the rest of the code
never has to touch the filesystem directly.
"""

from __future__ import annotations

import json
import os
from typing import List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "tracker.json")


def _ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_users(users: List) -> None:
    """
    Persist a list of User objects to the JSON data file.

    Args:
        users: List of User instances to serialize.
    """
    _ensure_data_dir()
    payload = [u.to_dict() for u in users]
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"Could not write data file: {exc}") from exc


def load_users() -> List:
    """
    Load and reconstruct User objects from the JSON data file.

    Returns:
        List of User instances, or an empty list if the file
        does not exist or contains invalid JSON.
    """
    # Import here to avoid circular imports at module level
    from models.user import User

    _ensure_data_dir()

    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[warning] Could not read data file ({exc}). Starting fresh.")
        return []

    # Rebuild the in-memory objects
    User.clear_registry()
    users = []
    for u_data in payload:
        try:
            users.append(User.from_dict(u_data))
        except (KeyError, ValueError) as exc:
            print(f"[warning] Skipping malformed user record: {exc}")

    return users


def data_file_path() -> str:
    """Return the absolute path of the active data file."""
    return DATA_FILE