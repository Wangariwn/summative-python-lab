"""
models/project.py
-----------------
Project model – sits between User (owner) and Task (children).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from models.task import Task


class Project:
    """
    Represents a development project owned by a User.

    Attributes:
        project_id  (str) : Auto-generated unique identifier.
        title       (str) : Project name.
        description (str) : Optional long-form description.
        due_date    (str) : ISO date string (YYYY-MM-DD).
        owner       (str) : Username of the owning user.
        tasks       (list): List of Task objects.
        created_at  (str) : ISO-formatted creation timestamp.
    """

    def __init__(
        self,
        title: str,
        owner: str,
        description: str = "",
        due_date: str = "",
        project_id: str | None = None,
        created_at: str | None = None,
    ):
        self._project_id = project_id or str(uuid.uuid4())[:8]
        self._title = title
        self.owner = owner
        self.description = description
        self._due_date = due_date
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self._tasks: List[Task] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def project_id(self) -> str:
        """Unique project identifier (read-only after creation)."""
        return self._project_id

    @property
    def title(self) -> str:
        """Project title."""
        return self._title

    @title.setter
    def title(self, value: str):
        """Set title after validation."""
        if not value or not value.strip():
            raise ValueError("Project title cannot be empty.")
        self._title = value.strip()

    @property
    def due_date(self) -> str:
        """Due date string (YYYY-MM-DD)."""
        return self._due_date

    @due_date.setter
    def due_date(self, value: str):
        """Validate and set the due date."""
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date format {value!r}. Use YYYY-MM-DD."
                )
        self._due_date = value

    @property
    def tasks(self) -> List[Task]:
        """Return a copy of the task list."""
        return list(self._tasks)

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Append a Task to this project."""
        self._tasks.append(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Return the Task with the given ID, or None."""
        for t in self._tasks:
            if t.task_id == task_id:
                return t
        return None

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if removed."""
        for i, t in enumerate(self._tasks):
            if t.task_id == task_id:
                del self._tasks[i]
                return True
        return False

    # ------------------------------------------------------------------
    # Statistics helpers
    # ------------------------------------------------------------------

    def completion_rate(self) -> float:
        """Return percentage of done tasks (0.0 – 100.0)."""
        if not self._tasks:
            return 0.0
        done = sum(1 for t in self._tasks if t.is_done())
        return round(done / len(self._tasks) * 100, 1)

    def task_summary(self) -> dict:
        """Return counts broken down by status."""
        summary = {"todo": 0, "in_progress": 0, "done": 0}
        for t in self._tasks:
            summary[t.status] = summary.get(t.status, 0) + 1
        return summary

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the project (and its tasks) to a plain dictionary."""
        return {
            "project_id": self._project_id,
            "title": self._title,
            "owner": self.owner,
            "description": self.description,
            "due_date": self._due_date,
            "created_at": self.created_at,
            "tasks": [t.to_dict() for t in self._tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Reconstruct a Project (and its Tasks) from a dictionary."""
        proj = cls(
            title=data["title"],
            owner=data["owner"],
            description=data.get("description", ""),
            due_date=data.get("due_date", ""),
            project_id=data.get("project_id"),
            created_at=data.get("created_at"),
        )
        for t_data in data.get("tasks", []):
            proj.add_task(Task.from_dict(t_data))
        return proj

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        due = f" | Due: {self._due_date}" if self._due_date else ""
        return (
            f"[{self._project_id}] {self._title} (owner: {self.owner})"
            f"{due} — {len(self._tasks)} task(s)"
        )

    def __repr__(self) -> str:
        return f"Project(id={self._project_id!r}, title={self._title!r}, owner={self.owner!r})"