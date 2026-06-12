"""
models/task.py
--------------
Task model – the leaf node of the data hierarchy.
Each Task belongs to exactly one Project.
"""

from __future__ import annotations

import uuid
from datetime import datetime


class Task:
    """
    Represents a single unit of work within a project.

    Attributes:
        task_id   (str)  : Auto-generated unique identifier.
        title     (str)  : Short description of the task.
        status    (str)  : One of 'todo', 'in_progress', 'done'.
        assigned_to (str): Name of the user responsible for the task.
        created_at (str) : ISO-formatted creation timestamp.
    """

    VALID_STATUSES = ("todo", "in_progress", "done")

    # Class-level counter used for display ordering (not persistence key)
    _count: int = 0

    def __init__(
        self,
        title: str,
        assigned_to: str = "Unassigned",
        status: str = "todo",
        task_id: str | None = None,
        created_at: str | None = None,
    ):
        Task._count += 1
        self._task_id = task_id or str(uuid.uuid4())[:8]
        self.title = title
        self.assigned_to = assigned_to
        self._status = status
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def task_id(self) -> str:
        """Unique task identifier (read-only after creation)."""
        return self._task_id

    @property
    def status(self) -> str:
        """Current status of the task."""
        return self._status

    @status.setter
    def status(self, value: str):
        """Validate and set the task status."""
        if value not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status {value!r}. Choose from {self.VALID_STATUSES}."
            )
        self._status = value

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def complete(self):
        """Mark this task as done."""
        self._status = "done"

    def start(self):
        """Mark this task as in-progress."""
        self._status = "in_progress"

    def is_done(self) -> bool:
        """Return True if the task is completed."""
        return self._status == "done"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary (for JSON storage)."""
        return {
            "task_id": self._task_id,
            "title": self.title,
            "status": self._status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Reconstruct a Task from a dictionary loaded from JSON."""
        return cls(
            title=data["title"],
            assigned_to=data.get("assigned_to", "Unassigned"),
            status=data.get("status", "todo"),
            task_id=data.get("task_id"),
            created_at=data.get("created_at"),
        )

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        status_icon = {"todo": "○", "in_progress": "◑", "done": "●"}.get(
            self._status, "?"
        )
        return f"[{self._task_id}] {status_icon} {self.title} (→ {self.assigned_to})"

    def __repr__(self) -> str:
        return (
            f"Task(id={self._task_id!r}, title={self.title!r}, status={self._status!r})"
        )