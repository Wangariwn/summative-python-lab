"""
utils/display.py
----------------
Terminal display helpers built on top of tabulate and colorama.

We purposely keep all display logic here so that the CLI layer stays
thin and the display style can be changed in one place.
"""

from __future__ import annotations

import os
from typing import List

from tabulate import tabulate
import colorama
from colorama import Fore, Style

# Initialise colorama once at import time (handles Windows ANSI codes)
colorama.init(autoreset=True)

# ── Colour aliases ────────────────────────────────────────────────────
HEADER = Fore.CYAN + Style.BRIGHT
SUCCESS = Fore.GREEN + Style.BRIGHT
WARNING = Fore.YELLOW + Style.BRIGHT
ERROR = Fore.RED + Style.BRIGHT
DIM = Style.DIM
RESET = Style.RESET_ALL

TABLE_FMT = "rounded_outline"  # tabulate table style


# ── Generic helpers ───────────────────────────────────────────────────

def banner(text: str) -> None:
    """Print a highlighted section banner."""
    try:
        width = min(os.get_terminal_size().columns, 72)
    except OSError:
        width = 72
    print()
    print(HEADER + "═" * width)
    print(HEADER + f"  {text}")
    print(HEADER + "═" * width)
    print()


def ok(msg: str) -> None:
    """Print a success message."""
    print(SUCCESS + f"✔  {msg}")


def warn(msg: str) -> None:
    """Print a warning message."""
    print(WARNING + f"⚠  {msg}")


def err(msg: str) -> None:
    """Print an error message."""
    print(ERROR + f"✖  {msg}")


def info(msg: str) -> None:
    """Print an informational message."""
    print(Fore.BLUE + f"ℹ  {msg}" + RESET)


# ── Entity display helpers ────────────────────────────────────────────

def show_users(users: List) -> None:
    """
    Render all users as a table.

    Args:
        users: List of User objects.
    """
    if not users:
        warn("No users found.")
        return

    rows = []
    for u in users:
        rows.append([
            Fore.CYAN + u.user_id + RESET,
            u.name,
            u.email,
            u.role,
            str(len(u.projects)),
            u.created_at[:10],
        ])

    headers = ["ID", "Name", "Email", "Role", "Projects", "Created"]
    banner("Users")
    print(tabulate(rows, headers=headers, tablefmt=TABLE_FMT))
    print()


def show_projects(projects: List, title: str = "Projects") -> None:
    """
    Render a list of projects as a table.

    Args:
        projects: List of Project objects.
        title   : Section banner title.
    """
    if not projects:
        warn("No projects found.")
        return

    rows = []
    for p in projects:
        summary = p.task_summary()
        progress_bar = _progress_bar(p.completion_rate())
        rows.append([
            Fore.CYAN + p.project_id + RESET,
            p.title,
            p.owner,
            p.due_date or "—",
            str(len(p.tasks)),
            progress_bar,
            p.created_at[:10],
        ])

    headers = ["ID", "Title", "Owner", "Due", "Tasks", "Progress", "Created"]
    banner(title)
    print(tabulate(rows, headers=headers, tablefmt=TABLE_FMT))
    print()


def show_tasks(tasks: List, project_title: str = "") -> None:
    """
    Render a list of tasks as a table.

    Args:
        tasks        : List of Task objects.
        project_title: Optional project name for the banner.
    """
    heading = f"Tasks — {project_title}" if project_title else "Tasks"
    if not tasks:
        warn(f"No tasks in project '{project_title}'.")
        return

    status_colours = {
        "todo": Fore.WHITE,
        "in_progress": Fore.YELLOW,
        "done": Fore.GREEN,
    }
    status_icons = {"todo": "○", "in_progress": "◑", "done": "●"}

    rows = []
    for t in tasks:
        col = status_colours.get(t.status, "")
        icon = status_icons.get(t.status, "?")
        rows.append([
            Fore.CYAN + t.task_id + RESET,
            t.title,
            col + f"{icon} {t.status}" + RESET,
            t.assigned_to,
            t.created_at[:10],
        ])

    headers = ["ID", "Title", "Status", "Assigned To", "Created"]
    banner(heading)
    print(tabulate(rows, headers=headers, tablefmt=TABLE_FMT))
    print()


def show_project_detail(project) -> None:
    """
    Show full detail for a single project including its tasks.

    Args:
        project: A Project object.
    """
    banner(f"Project Detail — {project.title}")
    details = [
        ["ID", project.project_id],
        ["Title", project.title],
        ["Owner", project.owner],
        ["Description", project.description or "—"],
        ["Due Date", project.due_date or "—"],
        ["Created", project.created_at[:10]],
        ["Completion", f"{project.completion_rate():.1f}%"],
    ]
    print(tabulate(details, tablefmt="simple"))
    print()
    show_tasks(project.tasks, project.title)


# ── Internal helpers ──────────────────────────────────────────────────

def _progress_bar(pct: float, width: int = 10) -> str:
    """Return a coloured ASCII progress bar string."""
    filled = int(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    colour = Fore.GREEN if pct == 100 else (Fore.YELLOW if pct > 0 else Fore.WHITE)
    return colour + f"{bar} {pct:5.1f}%" + RESET