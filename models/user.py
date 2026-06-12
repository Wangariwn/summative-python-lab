"""
models/user.py
--------------
User model – top of the data hierarchy.
Extends Person to demonstrate inheritance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from models.person import Person
from models.project import Project


class User(Person):
    """
    Represents a system user who owns one or more projects.

    Inherits name and email from Person.

    Attributes:
        user_id    (str) : Auto-generated unique identifier.
        role       (str) : 'admin' or 'developer'.
        created_at (str) : ISO-formatted creation timestamp.
        projects   (list): Projects owned by this user.
    """

    # Class-level registry so we can look users up without loading JSON each time
    _registry: dict[str, "User"] = {}

    VALID_ROLES = ("admin", "developer")

    def __init__(
        self,
        name: str,
        email: str,
        role: str = "developer",
        user_id: str | None = None,
        created_at: str | None = None,
    ):
        super().__init__(name, email)
        self._user_id = user_id or str(uuid.uuid4())[:8]
        self._role = role
        self.created_at = created_at or datetime.now().isoformat(timespec="seconds")
        self._projects: List[Project] = []

        # Register in class-level dict
        User._registry[self._user_id] = self

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def user_id(self) -> str:
        """Unique user identifier (read-only after creation)."""
        return self._user_id

    @property
    def role(self) -> str:
        """User role ('admin' or 'developer')."""
        return self._role

    @role.setter
    def role(self, value: str):
        """Set role after validation."""
        if value not in self.VALID_ROLES:
            raise ValueError(f"Role must be one of {self.VALID_ROLES}.")
        self._role = value

    @property
    def projects(self) -> List[Project]:
        """Return a copy of the project list."""
        return list(self._projects)

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional["User"]:
        """Look up a User by their ID from the class registry."""
        return cls._registry.get(user_id)

    @classmethod
    def clear_registry(cls):
        """Reset the registry (used when reloading from disk)."""
        cls._registry.clear()

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------

    def add_project(self, project: Project) -> None:
        """Attach a Project to this user."""
        self._projects.append(project)

    def get_project(self, project_id: str) -> Optional[Project]:
        """Return the Project with the given ID, or None."""
        for p in self._projects:
            if p.project_id == project_id:
                return p
        return None

    def find_project_by_title(self, title: str) -> Optional[Project]:
        """Case-insensitive search for a project by title."""
        for p in self._projects:
            if p.title.lower() == title.lower():
                return p
        return None

    def remove_project(self, project_id: str) -> bool:
        """Remove a project by ID. Returns True if removed."""
        for i, p in enumerate(self._projects):
            if p.project_id == project_id:
                del self._projects[i]
                return True
        return False

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the user (and their projects) to a plain dictionary."""
        return {
            "user_id": self._user_id,
            "name": self._name,
            "email": self._email,
            "role": self._role,
            "created_at": self.created_at,
            "projects": [p.to_dict() for p in self._projects],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Reconstruct a User (and their Projects/Tasks) from a dictionary."""
        user = cls(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "developer"),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
        )
        for p_data in data.get("projects", []):
            user.add_project(Project.from_dict(p_data))
        return user

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return (
            f"[{self._user_id}] {self._name} <{self._email}> "
            f"({self._role}) — {len(self._projects)} project(s)"
        )

    def __repr__(self) -> str:
        return f"User(id={self._user_id!r}, name={self._name!r}, role={self._role!r})"