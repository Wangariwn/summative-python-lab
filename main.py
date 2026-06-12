#!/usr/bin/env python3
"""
main.py
-------
CLI entry point for the Project Tracker tool.

Usage examples:
  python main.py add-user --name "Alex" --email "alex@example.com"
  python main.py list-users
  python main.py add-project --user "Alex" --title "CLI Tool" --due 2025-12-31
  python main.py list-projects --user "Alex"
  python main.py add-task --project "CLI Tool" --title "Write tests" --assign "Alex"
  python main.py list-tasks --project "CLI Tool"
  python main.py complete-task --task "Write tests"
  python main.py show-project --project "CLI Tool"
  python main.py delete-user --user "Alex"
  python main.py search --query "CLI"
"""

from __future__ import annotations

import argparse
import sys

from models.user import User
from models.project import Project
from models.task import Task
from utils.storage import save_users, load_users
from utils.helpers import (
    validate_email,
    validate_date,
    find_user_by_name,
    find_user_by_id,
    find_project_globally,
    find_task_globally,
)
from utils.display import (
    ok, warn, err, info, banner,
    show_users, show_projects, show_tasks, show_project_detail,
)


# ── Shared state (loaded once at start-up) ────────────────────────────

def load_state() -> list:
    """Load users from disk and return the list."""
    return load_users()


def persist(users: list) -> None:
    """Save users back to disk."""
    save_users(users)


# ═══════════════════════════════════════════════════════════════════════
# Command handlers
# ═══════════════════════════════════════════════════════════════════════

def cmd_add_user(args, users: list) -> list:
    """
    Handle the 'add-user' subcommand.

    Creates a new User and persists it.
    """
    # Validate email
    if not validate_email(args.email):
        err(f"Invalid email address: {args.email!r}")
        sys.exit(1)

    # Duplicate name check
    if find_user_by_name(users, args.name):
        err(f"A user named {args.name!r} already exists.")
        sys.exit(1)

    role = args.role or "developer"
    if role not in User.VALID_ROLES:
        err(f"Role must be one of {User.VALID_ROLES}.")
        sys.exit(1)

    user = User(name=args.name, email=args.email, role=role)
    users.append(user)
    persist(users)
    ok(f"User '{user.name}' created (ID: {user.user_id}).")
    return users


def cmd_list_users(args, users: list) -> None:
    """Handle the 'list-users' subcommand. Displays all users."""
    show_users(users)


def cmd_delete_user(args, users: list) -> list:
    """
    Handle the 'delete-user' subcommand.

    Removes a user and all their associated data.
    """
    user = find_user_by_name(users, args.user) or find_user_by_id(users, args.user)
    if not user:
        err(f"User {args.user!r} not found.")
        sys.exit(1)

    users.remove(user)
    persist(users)
    ok(f"User '{user.name}' deleted.")
    return users


def cmd_add_project(args, users: list) -> list:
    """
    Handle the 'add-project' subcommand.

    Creates a new Project and attaches it to the specified user.
    """
    user = find_user_by_name(users, args.user) or find_user_by_id(users, args.user)
    if not user:
        err(f"User {args.user!r} not found. Create them first with 'add-user'.")
        sys.exit(1)

    # Duplicate project title check (per-user)
    if user.find_project_by_title(args.title):
        err(f"User '{user.name}' already has a project titled {args.title!r}.")
        sys.exit(1)

    # Due date validation
    if args.due and not validate_date(args.due):
        err(f"Due date {args.due!r} must be in YYYY-MM-DD format.")
        sys.exit(1)

    project = Project(
        title=args.title,
        owner=user.name,
        description=args.description or "",
        due_date=args.due or "",
    )
    user.add_project(project)
    persist(users)
    ok(f"Project '{project.title}' created (ID: {project.project_id}) for '{user.name}'.")
    return users


def cmd_list_projects(args, users: list) -> None:
    """
    Handle the 'list-projects' subcommand.

    Shows all projects, or projects for a specific user.
    """
    if args.user:
        user = find_user_by_name(users, args.user) or find_user_by_id(users, args.user)
        if not user:
            err(f"User {args.user!r} not found.")
            sys.exit(1)
        show_projects(user.projects, title=f"Projects for {user.name}")
    else:
        all_projects = [p for u in users for p in u.projects]
        show_projects(all_projects)


def cmd_show_project(args, users: list) -> None:
    """
    Handle the 'show-project' subcommand.

    Displays full detail (description, tasks) for a single project.
    """
    _, project = find_project_globally(users, args.project)
    if not project:
        err(f"Project {args.project!r} not found.")
        sys.exit(1)
    show_project_detail(project)


def cmd_edit_project(args, users: list) -> list:
    """
    Handle the 'edit-project' subcommand.

    Updates title, description, or due_date of an existing project.
    """
    _, project = find_project_globally(users, args.project)
    if not project:
        err(f"Project {args.project!r} not found.")
        sys.exit(1)

    changed = False
    if args.title:
        project.title = args.title
        changed = True
    if args.description is not None:
        project.description = args.description
        changed = True
    if args.due:
        if not validate_date(args.due):
            err(f"Due date {args.due!r} must be in YYYY-MM-DD format.")
            sys.exit(1)
        project.due_date = args.due
        changed = True

    if not changed:
        warn("No changes specified. Use --title, --description, or --due.")
        return users

    persist(users)
    ok(f"Project '{project.title}' updated.")
    return users


def cmd_delete_project(args, users: list) -> list:
    """
    Handle the 'delete-project' subcommand.

    Removes a project from its owner.
    """
    user, project = find_project_globally(users, args.project)
    if not project:
        err(f"Project {args.project!r} not found.")
        sys.exit(1)

    user.remove_project(project.project_id)
    persist(users)
    ok(f"Project '{project.title}' deleted.")
    return users


def cmd_add_task(args, users: list) -> list:
    """
    Handle the 'add-task' subcommand.

    Creates a Task and appends it to the specified project.
    """
    _, project = find_project_globally(users, args.project)
    if not project:
        err(f"Project {args.project!r} not found.")
        sys.exit(1)

    task = Task(
        title=args.title,
        assigned_to=args.assign or "Unassigned",
        status=args.status or "todo",
    )
    project.add_task(task)
    persist(users)
    ok(f"Task '{task.title}' added to project '{project.title}' (ID: {task.task_id}).")
    return users


def cmd_list_tasks(args, users: list) -> None:
    """
    Handle the 'list-tasks' subcommand.

    Displays tasks for a given project, with optional status filter.
    """
    _, project = find_project_globally(users, args.project)
    if not project:
        err(f"Project {args.project!r} not found.")
        sys.exit(1)

    tasks = project.tasks
    if args.status:
        tasks = [t for t in tasks if t.status == args.status]
        if not tasks:
            warn(f"No tasks with status '{args.status}'.")
            return

    show_tasks(tasks, project.title)


def cmd_complete_task(args, users: list) -> list:
    """
    Handle the 'complete-task' subcommand.

    Marks a task as 'done'.
    """
    _, task = find_task_globally(users, args.task)
    if not task:
        err(f"Task {args.task!r} not found.")
        sys.exit(1)

    if task.is_done():
        warn(f"Task '{task.title}' is already marked as done.")
        return users

    task.complete()
    persist(users)
    ok(f"Task '{task.title}' marked as complete.")
    return users


def cmd_update_task(args, users: list) -> list:
    """
    Handle the 'update-task' subcommand.

    Change a task's status or reassign it.
    """
    _, task = find_task_globally(users, args.task)
    if not task:
        err(f"Task {args.task!r} not found.")
        sys.exit(1)

    changed = False
    if args.status:
        try:
            task.status = args.status
            changed = True
        except ValueError as exc:
            err(str(exc))
            sys.exit(1)
    if args.assign:
        task.assigned_to = args.assign
        changed = True
    if args.title:
        task.title = args.title
        changed = True

    if not changed:
        warn("No changes specified. Use --status, --assign, or --title.")
        return users

    persist(users)
    ok(f"Task updated: {task}")
    return users


def cmd_delete_task(args, users: list) -> list:
    """
    Handle the 'delete-task' subcommand.

    Removes a task from its parent project.
    """
    project, task = find_task_globally(users, args.task)
    if not task:
        err(f"Task {args.task!r} not found.")
        sys.exit(1)

    project.remove_task(task.task_id)
    persist(users)
    ok(f"Task '{task.title}' deleted from project '{project.title}'.")
    return users


def cmd_search(args, users: list) -> None:
    """
    Handle the 'search' subcommand.

    Searches users, projects, and tasks for the query string.
    """
    q = args.query.lower()
    banner(f"Search results for: '{args.query}'")

    matched_users = [u for u in users if q in u.name.lower() or q in u.email.lower()]
    matched_projects = [
        p for u in users for p in u.projects
        if q in p.title.lower() or q in p.description.lower()
    ]
    matched_tasks = [
        t for u in users for p in u.projects for t in p.tasks
        if q in t.title.lower()
    ]

    if matched_users:
        show_users(matched_users)
    if matched_projects:
        show_projects(matched_projects, title="Matching Projects")
    if matched_tasks:
        show_tasks(matched_tasks, "Matching Tasks")

    if not any([matched_users, matched_projects, matched_tasks]):
        warn(f"No results found for '{args.query}'.")


def cmd_stats(args, users: list) -> None:
    """
    Handle the 'stats' subcommand.

    Shows a summary dashboard of the whole tracker.
    """
    from colorama import Fore, Style
    from tabulate import tabulate

    all_projects = [p for u in users for p in u.projects]
    all_tasks = [t for p in all_projects for t in p.tasks]

    banner("📊 System Statistics")

    rows = [
        ["Total Users", len(users)],
        ["Total Projects", len(all_projects)],
        ["Total Tasks", len(all_tasks)],
        ["Tasks Done", sum(1 for t in all_tasks if t.is_done())],
        ["Tasks In Progress", sum(1 for t in all_tasks if t.status == "in_progress")],
        ["Tasks To Do", sum(1 for t in all_tasks if t.status == "todo")],
    ]
    print(tabulate(rows, headers=["Metric", "Count"], tablefmt="rounded_outline"))
    print()

    if all_projects:
        print(Fore.CYAN + Style.BRIGHT + "  Per-project completion:" + Style.RESET_ALL)
        for p in all_projects:
            bar_width = 20
            pct = p.completion_rate()
            filled = int(pct / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"  {p.title:<30} {bar} {pct:5.1f}%")
        print()


# ═══════════════════════════════════════════════════════════════════════
# Argument parser construction
# ═══════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level ArgumentParser with all subcommands."""

    parser = argparse.ArgumentParser(
        prog="tracker",
        description="🗂  Multi-user Project Tracker CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py add-user --name "Alex" --email "alex@example.com"
  python main.py add-project --user "Alex" --title "CLI Tool" --due 2025-12-31
  python main.py add-task --project "CLI Tool" --title "Write README" --assign "Alex"
  python main.py complete-task --task "Write README"
  python main.py stats
        """,
    )

    subs = parser.add_subparsers(dest="command", metavar="COMMAND")
    subs.required = True

    # ── User commands ─────────────────────────────────────────────────

    p_add_user = subs.add_parser("add-user", help="Create a new user")
    p_add_user.add_argument("--name", required=True, help="Full name of the user")
    p_add_user.add_argument("--email", required=True, help="Email address")
    p_add_user.add_argument(
        "--role", choices=User.VALID_ROLES, default="developer", help="User role"
    )

    subs.add_parser("list-users", help="List all users")

    p_del_user = subs.add_parser("delete-user", help="Remove a user")
    p_del_user.add_argument("--user", required=True, help="User name or ID")

    # ── Project commands ──────────────────────────────────────────────

    p_add_proj = subs.add_parser("add-project", help="Create a project for a user")
    p_add_proj.add_argument("--user", required=True, help="Owner name or ID")
    p_add_proj.add_argument("--title", required=True, help="Project title")
    p_add_proj.add_argument("--description", default="", help="Project description")
    p_add_proj.add_argument("--due", default="", help="Due date (YYYY-MM-DD)")

    p_list_proj = subs.add_parser("list-projects", help="List projects")
    p_list_proj.add_argument("--user", default="", help="Filter by user name or ID")

    p_show_proj = subs.add_parser("show-project", help="Show project details")
    p_show_proj.add_argument("--project", required=True, help="Project title or ID")

    p_edit_proj = subs.add_parser("edit-project", help="Edit a project")
    p_edit_proj.add_argument("--project", required=True, help="Project title or ID")
    p_edit_proj.add_argument("--title", default="", help="New title")
    p_edit_proj.add_argument("--description", default=None, help="New description")
    p_edit_proj.add_argument("--due", default="", help="New due date (YYYY-MM-DD)")

    p_del_proj = subs.add_parser("delete-project", help="Remove a project")
    p_del_proj.add_argument("--project", required=True, help="Project title or ID")

    # ── Task commands ─────────────────────────────────────────────────

    p_add_task = subs.add_parser("add-task", help="Add a task to a project")
    p_add_task.add_argument("--project", required=True, help="Project title or ID")
    p_add_task.add_argument("--title", required=True, help="Task title")
    p_add_task.add_argument("--assign", default="Unassigned", help="Assigned user name")
    p_add_task.add_argument(
        "--status", choices=Task.VALID_STATUSES, default="todo", help="Initial status"
    )

    p_list_tasks = subs.add_parser("list-tasks", help="List tasks in a project")
    p_list_tasks.add_argument("--project", required=True, help="Project title or ID")
    p_list_tasks.add_argument(
        "--status", choices=Task.VALID_STATUSES, default="", help="Filter by status"
    )

    p_complete = subs.add_parser("complete-task", help="Mark a task as done")
    p_complete.add_argument("--task", required=True, help="Task title or ID")

    p_update_task = subs.add_parser("update-task", help="Update a task")
    p_update_task.add_argument("--task", required=True, help="Task title or ID")
    p_update_task.add_argument("--title", default="", help="New title")
    p_update_task.add_argument(
        "--status", choices=Task.VALID_STATUSES, default="", help="New status"
    )
    p_update_task.add_argument("--assign", default="", help="Reassign to user")

    p_del_task = subs.add_parser("delete-task", help="Remove a task")
    p_del_task.add_argument("--task", required=True, help="Task title or ID")

    # ── Search & stats ────────────────────────────────────────────────

    p_search = subs.add_parser("search", help="Search across all entities")
    p_search.add_argument("--query", required=True, help="Search query")

    subs.add_parser("stats", help="Show system-wide statistics")

    return parser


# ═══════════════════════════════════════════════════════════════════════
# Main dispatch
# ═══════════════════════════════════════════════════════════════════════

COMMAND_MAP = {
    "add-user": cmd_add_user,
    "list-users": cmd_list_users,
    "delete-user": cmd_delete_user,
    "add-project": cmd_add_project,
    "list-projects": cmd_list_projects,
    "show-project": cmd_show_project,
    "edit-project": cmd_edit_project,
    "delete-project": cmd_delete_project,
    "add-task": cmd_add_task,
    "list-tasks": cmd_list_tasks,
    "complete-task": cmd_complete_task,
    "update-task": cmd_update_task,
    "delete-task": cmd_delete_task,
    "search": cmd_search,
    "stats": cmd_stats,
}

# Commands that mutate state (return updated user list)
MUTATING_COMMANDS = {
    "add-user", "delete-user",
    "add-project", "edit-project", "delete-project",
    "add-task", "complete-task", "update-task", "delete-task",
}


def main() -> None:
    """Parse arguments, load state, dispatch command, save state."""
    parser = build_parser()
    args = parser.parse_args()

    users = load_state()

    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        err(f"Unknown command: {args.command}")
        sys.exit(1)

    result = handler(args, users)

    # Mutating commands return the (possibly modified) user list
    if args.command in MUTATING_COMMANDS and result is not None:
        users = result


if __name__ == "__main__":
    main()