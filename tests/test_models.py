"""
tests/test_models.py
--------------------
Unit tests for User, Project, Task, and helper functions.

Run with:
  python -m pytest tests/ -v
  # or
  python -m unittest discover -s tests
"""

import sys
import os
import json
import tempfile
import unittest

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.person import Person
from models.task import Task
from models.project import Project
from models.user import User
from utils.helpers import (
    validate_email,
    validate_date,
    find_user_by_name,
    find_user_by_id,
    find_project_globally,
    find_task_globally,
    truncate,
)


# ═══════════════════════════════════════════════════════════════════════
# Person tests
# ═══════════════════════════════════════════════════════════════════════

class TestPerson(unittest.TestCase):
    """Tests for the Person base class."""

    def test_init(self):
        p = Person("Alice", "alice@example.com")
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.email, "alice@example.com")

    def test_name_setter_strips_whitespace(self):
        p = Person("  Bob  ", "bob@example.com")
        p.name = "  Carol  "
        self.assertEqual(p.name, "Carol")

    def test_name_setter_rejects_empty(self):
        p = Person("Dave", "dave@example.com")
        with self.assertRaises(ValueError):
            p.name = ""

    def test_email_setter_invalid(self):
        p = Person("Eve", "eve@example.com")
        with self.assertRaises(ValueError):
            p.email = "not-an-email"

    def test_repr(self):
        p = Person("Frank", "frank@example.com")
        self.assertIn("Frank", repr(p))


# ═══════════════════════════════════════════════════════════════════════
# Task tests
# ═══════════════════════════════════════════════════════════════════════

class TestTask(unittest.TestCase):
    """Tests for the Task model."""

    def setUp(self):
        self.task = Task(title="Write tests", assigned_to="Grace")

    def test_default_status(self):
        self.assertEqual(self.task.status, "todo")

    def test_complete(self):
        self.task.complete()
        self.assertTrue(self.task.is_done())
        self.assertEqual(self.task.status, "done")

    def test_start(self):
        self.task.start()
        self.assertEqual(self.task.status, "in_progress")

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self.task.status = "flying"

    def test_task_id_generated(self):
        self.assertIsNotNone(self.task.task_id)
        self.assertTrue(len(self.task.task_id) > 0)

    def test_serialization_roundtrip(self):
        d = self.task.to_dict()
        restored = Task.from_dict(d)
        self.assertEqual(restored.title, self.task.title)
        self.assertEqual(restored.status, self.task.status)
        self.assertEqual(restored.task_id, self.task.task_id)

    def test_str_contains_title(self):
        self.assertIn("Write tests", str(self.task))


# ═══════════════════════════════════════════════════════════════════════
# Project tests
# ═══════════════════════════════════════════════════════════════════════

class TestProject(unittest.TestCase):
    """Tests for the Project model."""

    def setUp(self):
        self.project = Project(
            title="Alpha", owner="Henry", description="First project", due_date="2025-12-31"
        )

    def test_add_task(self):
        t = Task("Task A")
        self.project.add_task(t)
        self.assertEqual(len(self.project.tasks), 1)

    def test_get_task_by_id(self):
        t = Task("Task B")
        self.project.add_task(t)
        found = self.project.get_task(t.task_id)
        self.assertIs(found, t)

    def test_get_task_missing_returns_none(self):
        self.assertIsNone(self.project.get_task("nonexistent"))

    def test_remove_task(self):
        t = Task("Task C")
        self.project.add_task(t)
        result = self.project.remove_task(t.task_id)
        self.assertTrue(result)
        self.assertEqual(len(self.project.tasks), 0)

    def test_completion_rate_empty(self):
        self.assertEqual(self.project.completion_rate(), 0.0)

    def test_completion_rate_partial(self):
        t1 = Task("T1"); t1.complete()
        t2 = Task("T2")
        self.project.add_task(t1)
        self.project.add_task(t2)
        self.assertEqual(self.project.completion_rate(), 50.0)

    def test_completion_rate_full(self):
        t1 = Task("T1"); t1.complete()
        t2 = Task("T2"); t2.complete()
        self.project.add_task(t1)
        self.project.add_task(t2)
        self.assertEqual(self.project.completion_rate(), 100.0)

    def test_task_summary(self):
        t1 = Task("T1")
        t2 = Task("T2"); t2.complete()
        self.project.add_task(t1)
        self.project.add_task(t2)
        s = self.project.task_summary()
        self.assertEqual(s["todo"], 1)
        self.assertEqual(s["done"], 1)

    def test_invalid_due_date_raises(self):
        with self.assertRaises(ValueError):
            self.project.due_date = "31/12/2025"

    def test_serialization_roundtrip(self):
        t = Task("Roundtrip task")
        self.project.add_task(t)
        d = self.project.to_dict()
        restored = Project.from_dict(d)
        self.assertEqual(restored.title, "Alpha")
        self.assertEqual(len(restored.tasks), 1)
        self.assertEqual(restored.tasks[0].title, "Roundtrip task")

    def test_str_contains_title(self):
        self.assertIn("Alpha", str(self.project))


# ═══════════════════════════════════════════════════════════════════════
# User tests
# ═══════════════════════════════════════════════════════════════════════

class TestUser(unittest.TestCase):
    """Tests for the User model (extends Person)."""

    def setUp(self):
        User.clear_registry()
        self.user = User(name="Isla", email="isla@example.com", role="admin")

    def test_inherits_from_person(self):
        from models.person import Person
        self.assertIsInstance(self.user, Person)

    def test_default_role(self):
        User.clear_registry()
        u = User("Jack", "jack@example.com")
        self.assertEqual(u.role, "developer")

    def test_invalid_role_raises(self):
        with self.assertRaises(ValueError):
            self.user.role = "superuser"

    def test_add_and_get_project(self):
        p = Project("Beta", owner="Isla")
        self.user.add_project(p)
        found = self.user.get_project(p.project_id)
        self.assertIs(found, p)

    def test_find_project_by_title(self):
        p = Project("Gamma", owner="Isla")
        self.user.add_project(p)
        found = self.user.find_project_by_title("gamma")  # case-insensitive
        self.assertIs(found, p)

    def test_remove_project(self):
        p = Project("Delta", owner="Isla")
        self.user.add_project(p)
        result = self.user.remove_project(p.project_id)
        self.assertTrue(result)
        self.assertEqual(len(self.user.projects), 0)

    def test_registry(self):
        found = User.get_by_id(self.user.user_id)
        self.assertIs(found, self.user)

    def test_serialization_roundtrip(self):
        p = Project("Epsilon", owner="Isla")
        t = Task("Task X")
        p.add_task(t)
        self.user.add_project(p)

        d = self.user.to_dict()
        User.clear_registry()
        restored = User.from_dict(d)
        self.assertEqual(restored.name, "Isla")
        self.assertEqual(len(restored.projects), 1)
        self.assertEqual(len(restored.projects[0].tasks), 1)

    def test_str_contains_name(self):
        self.assertIn("Isla", str(self.user))


# ═══════════════════════════════════════════════════════════════════════
# Helper function tests
# ═══════════════════════════════════════════════════════════════════════

class TestHelpers(unittest.TestCase):
    """Tests for utility helper functions."""

    def setUp(self):
        User.clear_registry()
        self.user = User("Karen", "karen@example.com")
        proj = Project("Zeta", owner="Karen")
        task = Task("Do something")
        proj.add_task(task)
        self.user.add_project(proj)
        self.users = [self.user]
        self.proj = proj
        self.task = task

    def test_validate_email_valid(self):
        self.assertTrue(validate_email("a@b.com"))

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email("not-an-email"))
        self.assertFalse(validate_email("@domain.com"))

    def test_validate_date_valid(self):
        self.assertTrue(validate_date("2025-12-31"))

    def test_validate_date_invalid(self):
        self.assertFalse(validate_date("31/12/2025"))
        self.assertFalse(validate_date("2025-13-01"))

    def test_find_user_by_name(self):
        found = find_user_by_name(self.users, "Karen")
        self.assertIs(found, self.user)

    def test_find_user_by_name_case_insensitive(self):
        found = find_user_by_name(self.users, "karen")
        self.assertIs(found, self.user)

    def test_find_user_by_name_missing(self):
        self.assertIsNone(find_user_by_name(self.users, "Nobody"))

    def test_find_user_by_id(self):
        found = find_user_by_id(self.users, self.user.user_id)
        self.assertIs(found, self.user)

    def test_find_project_globally_by_title(self):
        u, p = find_project_globally(self.users, "Zeta")
        self.assertIs(u, self.user)
        self.assertIs(p, self.proj)

    def test_find_project_globally_missing(self):
        u, p = find_project_globally(self.users, "Nonexistent")
        self.assertIsNone(u)
        self.assertIsNone(p)

    def test_find_task_globally(self):
        p, t = find_task_globally(self.users, "Do something")
        self.assertIs(p, self.proj)
        self.assertIs(t, self.task)

    def test_truncate_short(self):
        self.assertEqual(truncate("hi", 10), "hi")

    def test_truncate_long(self):
        result = truncate("A" * 50, 10)
        self.assertEqual(len(result), 10)
        self.assertTrue(result.endswith("…"))


# ═══════════════════════════════════════════════════════════════════════
# Storage / persistence tests
# ═══════════════════════════════════════════════════════════════════════

class TestStorage(unittest.TestCase):
    """Tests for the JSON persistence layer."""

    def setUp(self):
        User.clear_registry()

    def test_save_and_load_roundtrip(self):
        import utils.storage as storage

        # Override data file to a temp path
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        original_file = storage.DATA_FILE
        storage.DATA_FILE = tmp.name
        tmp.close()

        try:
            user = User("Liam", "liam@example.com")
            proj = Project("Theta", owner="Liam")
            task = Task("Persist me")
            proj.add_task(task)
            user.add_project(proj)

            storage.save_users([user])

            User.clear_registry()
            loaded = storage.load_users()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].name, "Liam")
            self.assertEqual(len(loaded[0].projects), 1)
            self.assertEqual(len(loaded[0].projects[0].tasks), 1)
        finally:
            storage.DATA_FILE = original_file
            os.unlink(tmp.name)

    def test_load_missing_file_returns_empty(self):
        import utils.storage as storage
        original_file = storage.DATA_FILE
        storage.DATA_FILE = "/tmp/__nonexistent_tracker_test__.json"
        try:
            result = storage.load_users()
            self.assertEqual(result, [])
        finally:
            storage.DATA_FILE = original_file

    def test_load_malformed_json_returns_empty(self):
        import utils.storage as storage
        tmp = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        )
        tmp.write("{ this is not valid JSON }")
        tmp.close()
        original_file = storage.DATA_FILE
        storage.DATA_FILE = tmp.name
        try:
            result = storage.load_users()
            self.assertEqual(result, [])
        finally:
            storage.DATA_FILE = original_file
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)