"""
models/person.py
----------------
Base class for any person entity in the system.
Demonstrates inheritance: User will extend Person.
"""


class Person:
    """
    Abstract-like base class representing a person.

    Attributes:
        name (str): Full name of the person.
        email (str): Email address of the person.
    """

    def __init__(self, name: str, email: str):
        self._name = name
        self._email = email

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the person's name."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set the person's name after validation."""
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value.strip()

    @property
    def email(self) -> str:
        """Return the person's email."""
        return self._email

    @email.setter
    def email(self, value: str):
        """Set the person's email after basic validation."""
        if "@" not in value:
            raise ValueError(f"Invalid email address: {value!r}")
        self._email = value.strip().lower()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, email={self._email!r})"