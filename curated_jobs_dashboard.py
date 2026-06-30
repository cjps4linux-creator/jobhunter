#!/usr/bin/env python3
"""
Curated Jobs Dashboard — Terminal TUI for managing Scout-delivered job listings.

Reads .md files from ~/Desktop/curated-jobs/, displays jobs in a Rich table,
and provides actions: Generate CV, Open URL, Delete, Refresh.

Designed for PS4 terminal (large text, keyboard-only, dark theme).
"""

import glob
import os
import re
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

# Ensure we can import rich when running system Python
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.style import Style
    from rich import box
except ImportError:
    # Fallback: try the hermes venv
    import importlib
    sys.path.insert(0, "/home/qba/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.style import Style
    from rich import box


# ── Configuration ──────────────────────────────────────────────────────────────
JOBS_DIR = Path("/home/qba/Desktop/curated-jobs")
CV_GENERATOR_SCRIPT = "/home/qba/jobhunter/terminal_cv_generator/run_app.sh"

# Theme colors
CYAN = "bold cyan"
PURPLE = "bold magenta"
DIM = "dim"
GREEN = "bold green"
YELLOW = "bold yellow"
RED = "bold red"
WHITE = "bold white"
GRAY = "grey62"

# Status indicators
STATUS_APPLIED = "✅"
STATUS_PENDING = "⏳"


# ── Job Parsing ────────────────────────────────────────────────────────────────
class Job:
    """Represents a single curated job listing."""

    def __init__(self, filepath: str, index: int):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.index = index
        self.company = "Unknown"
        self.role = "Unknown"
        self.salary = "Not disclosed"
        self.location = "Unknown"
        self.url = ""
        self.why = ""
        self.how_to_apply = ""
        self.status = STATUS_PENDING
        self.raw_content = ""
        self._parse()

    def _parse_entry(self, entry: str):
        """Parse a single job entry (bullet or header format)."""
        self.raw_content = entry

        # Try bullet format: - [ ] **Company** — Role
        bullet_match = re.search(r'- \[[ xX]\]\s*\*\*(.+?)\*\*\s*[—–-]\s*(.+)', entry)
        if bullet_match:
            self.company = bullet_match.group(1).strip()
            self.role = bullet_match.group(2).strip()

            # Status from checkbox
            if re.search(r'- \[[xX]\]', entry):
                self.status = STATUS_APPLIED

            # URL
            url_match = re.search(r'URL:\s*(https?://\S+)', entry)
            if url_match:
                self.url = url_match.group(1).strip()

            # Why
            why_match = re.search(r'Why:\s*(.+)', entry)
            if why_match:
                self.why = why_match.group(1).strip()

            # Fallback URL
            if not self.url:
                url_match = re.search(r'(https?://\S+)', entry)
                if url_match:
                    self.url = url_match.group(1).strip().rstrip(").,;")
            return

        # Try delivery format: ## N. Company — Role
        header_match = re.search(r'^##\s*\d+\.\s*(.+?)\s*[—–-]\s*(.+)', entry, re.MULTILINE)
        if header_match:
            self.company = header_match.group(1).strip()
            self.role = header_match.group(2).strip()

            # Salary (table format: **Salary** | value |)
            salary_match = re.search(r'\*\*Salary\*\*\s*\|\s*(.+?)\s*\|', entry)
            if salary_match:
                self.salary = salary_match.group(1).strip()

            # Location
            loc_match = re.search(r'\*\*Location\*\*\s*\|\s*(.+?)\s*\|', entry)
            if loc_match:
                self.location = loc_match.group(1).strip()

            # URL from "How to Apply" or any URL (with or without https://)
            url_match = re.search(r'(https?://\S+|[a-zA-Z0-9][\w\-]*\.(com|io|co|net|org|dev|app|za|ai|tech|xyz|me|info|biz|gov|edu)/[\w\-./%?&=#@+]*)', entry)
            if url_match:
                raw_url = url_match.group(1).strip().rstrip(").,;")
                # Add https:// if missing
                if not raw_url.startswith("http"):
                    raw_url = "https://" + raw_url
                self.url = raw_url

            # Why CJ Excels
            why_match = re.search(r'\*\*Why CJ Excels:\*\*\s*(.+)', entry)
            if why_match:
                self.why = why_match.group(1).strip()
            return

    def _parse(self):
        """Parse a single job entry from its .md file.

        Supports two formats:
        1. Curated format: Each file contains one job per bullet (- [ ] **Company** — Role)
        2. Delivery format: Full report with ## N. Company — Role headers
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.raw_content = content
        except (IOError, UnicodeDecodeError):
            return

        # Extract URL
        url_match = re.search(r'URL:\s*(https?://\S+)', content)
        if url_match:
            self.url = url_match.group(1).strip()

        # Extract Why
        why_match = re.search(r'Why:\s*(.+)', content)
        if why_match:
            self.why = why_match.group(1).strip()

        # Extract How to Apply
        how_match = re.search(r'How to Apply:\s*(.+)', content)
        if how_match:
            self.how_to_apply = how_match.group(1).strip()

        # Extract Salary
        salary_match = re.search(r'\*\*Salary\*\*\s*\|\s*(.+?)\s*\|', content)
        if salary_match:
            self.salary = salary_match.group(1).strip()

        # Extract Location
        loc_match = re.search(r'\*\*Location\*\*\s*\|\s*(.+?)\s*\|', content)
        if loc_match:
            self.location = loc_match.group(1).strip()

        # Extract Company + Role from bullet format: - [ ] **Company** — Role
        bullet_match = re.search(r'- \[[ xX]\]\s*\*\*(.+?)\*\*\s*[—–-]\s*(.+)', content)
        if bullet_match:
            self.company = bullet_match.group(1).strip()
            self.role = bullet_match.group(2).strip()
            # Status from checkbox
            if re.search(r'- \[[xX]\]', content):
                self.status = STATUS_APPLIED
            # Fallback URL from raw content
            if not self.url:
                url_match = re.search(r'(https?://\S+)', self.raw_content)
                if url_match:
                    self.url = url_match.group(1).strip().rstrip(").,;")
            return

        # Try delivery format: ## N. Company — Role
        header_match = re.search(r'##\s*\d+\.\s*(.+?)\s*[—–-]\s*(.+)', content)
        if header_match:
            self.company = header_match.group(1).strip()
            self.role = header_match.group(2).strip()
            if not self.url:
                url_match = re.search(r'(https?://\S+)', self.raw_content)
                if url_match:
                    self.url = url_match.group(1).strip().rstrip(").,;")

    @property
    def description(self) -> str:
        """Full description for CV generator input."""
        parts = [f"{self.company} — {self.role}"]
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.why:
            parts.append(self.why)
        if self.how_to_apply:
            parts.append(self.how_to_apply)
        return ". ".join(parts)


def load_jobs() -> list:
    """Load all curated jobs from the jobs directory.

    Supports two file formats:
    1. One job per file (delivery format with ## N. headers)
    2. Multiple jobs per file (curated format with - [ ] bullets)
    """
    if not JOBS_DIR.exists():
        return []

    md_files = sorted(glob.glob(str(JOBS_DIR / "*.md")),
                   key=os.path.getmtime, reverse=True)

    jobs = []
    index = 1
    for filepath in md_files:
        # Check if file has multiple bullets (curated format)
        try:
            with open(filepath) as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            continue

        # Count bullet entries (curated format)
        # Detect format
        bullets = re.findall(r'- \[[ xX]\]\s*\*\*', content)
        headers = re.findall(r'^##\s*\d+\.', content, re.MULTILINE)

        if bullets:
            # Curated format: multiple jobs as bullet list
            entries = re.split(r'\n(?=- \[[ xX]\])', content)
            for entry in entries:
                if not re.search(r'- \[[ xX]\]', entry):
                    continue
                job = Job.__new__(Job)
                job.filepath = filepath
                job.filename = os.path.basename(filepath)
                job.index = index
                job.company = "Unknown"
                job.role = "Unknown"
                job.salary = "Not disclosed"
                job.location = "Unknown"
                job.url = ""
                job.why = ""
                job.how_to_apply = ""
                job.status = STATUS_PENDING
                job.raw_content = entry
                job._parse_entry(entry)
                jobs.append(job)
                index += 1
        elif headers:
            # Delivery format: multiple jobs as ## N. headers
            entries = re.split(r'\n(?=^##\s*\d+\.)', content, flags=re.MULTILINE)
            for entry in entries:
                if not re.search(r'^##\s*\d+\.', entry, re.MULTILINE):
                    continue
                job = Job.__new__(Job)
                job.filepath = filepath
                job.filename = os.path.basename(filepath)
                job.index = index
                job.company = "Unknown"
                job.role = "Unknown"
                job.salary = "Not disclosed"
                job.location = "Unknown"
                job.url = ""
                job.why = ""
                job.how_to_apply = ""
                job.status = STATUS_PENDING
                job.raw_content = entry
                job._parse_entry(entry)
                jobs.append(job)
                index += 1
        else:
            # Single job per file
            job = Job(filepath, index)
            jobs.append(job)
            index += 1

    # Deduplicate by URL (keep first occurrence)
    seen_urls = set()
    deduped = []
    for job in jobs:
        if job.url:
            normalized = job.url.rstrip("/").lower()
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
        deduped.append(job)

    # Re-index
    for i, job in enumerate(deduped, 1):
        job.index = i

    return deduped


# ── UI Rendering ──────────────────────────────────────────────────────────────
class JobsDashboard:
    """Terminal TUI for the curated jobs dashboard."""

    def __init__(self):
        self.console = Console()
        self.jobs = []
        self.selected_index = 0
        self.selected_action = None  # Currently highlighted action key
        self.message = ""
        self.message_style = Style()
        self.show_help = True
        self.actions = [
            ("G", "Generate CV"),
            ("O", "Open URL"),
            ("D", "Delete"),
            ("R", "Refresh"),
        ]
        self.action_keys = [a[0] for a in self.actions]
        self.action_index = 0
        self.mode = "navigate"  # "navigate" or "action"

    def refresh_jobs(self):
        """Reload jobs from disk."""
        self.jobs = load_jobs()
        if self.selected_index >= len(self.jobs):
            self.selected_index = max(0, len(self.jobs) - 1)
        self.message = f"Refreshed — {len(self.jobs)} jobs loaded"
        self.message_style = Style(color="green")

    def build_table(self) -> Table:
        """Build the Rich table for the job list."""
        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style=Style(color="white", bold=True, bgcolor="rgb(30,30,60)"),
            border_style=Style(color="bright_cyan"),
            pad_edge=False,
            padding=(0, 1),
            expand=True,
        )

        table.add_column("#", style=Style(color="bright_cyan", bold=True), width=4, justify="center")
        table.add_column("Company", style=Style(color="white", bold=True), width=18)
        table.add_column("Role", style=Style(color="grey85"), width=30)
        table.add_column("Salary", style=Style(color="bright_green"), width=14)
        table.add_column("Status", width=6, justify="center")

        if not self.jobs:
            table.add_row(
                "—",
                Text("No jobs yet", style=Style(color="grey50", italic=True)),
                Text("Waiting for Scout delivery...", style=Style(color="grey50", italic=True)),
                "—",
                "—",
            )
        else:
            for i, job in enumerate(self.jobs):
                if i == self.selected_index:
                    row_style = Style(bgcolor="rgb(40,40,80)", bold=True)
                    idx_style = Style(color="bright_cyan", bold=True, bgcolor="rgb(40,40,80)")
                else:
                    row_style = Style()
                    idx_style = Style(color="cyan")

                table.add_row(
                    Text(str(job.index), style=idx_style),
                    Text(job.company[:18], style=row_style + Style(color="white")),
                    Text(job.role[:30], style=row_style + Style(color="grey78")),
                    Text(job.salary[:14], style=row_style + Style(color="green")),
                    Text(job.status, style=row_style),
                    style=row_style if i == self.selected_index else None,
                )

        return table

    def build_detail_panel(self) -> Panel:
        """Build the detail panel for the selected job."""
        if not self.jobs:
            return Panel(
                Text("No jobs to display.\n\nScout will deliver jobs here.\nCheck ~/Desktop/curated-jobs/",
                     style=Style(color="grey50", italic=True), justify="center"),
                title=Text("📋 Job Details", style=Style(color="bright_cyan", bold=True)),
                border_style=Style(color="bright_cyan"),
                padding=(1, 2),
            )

        job = self.jobs[self.selected_index]

        # Build detail content
        content = Text()
        content.append(f"Company:  ", style=Style(color="bright_cyan", bold=True))
        content.append(f"{job.company}\n", style=Style(color="white", bold=True))
        content.append(f"Role:     ", style=Style(color="bright_cyan", bold=True))
        content.append(f"{job.role}\n", style=Style(color="white"))
        content.append(f"Salary:   ", style=Style(color="bright_cyan", bold=True))
        content.append(f"{job.salary}\n", style=Style(color="green"))
        content.append(f"Location: ", style=Style(color="bright_cyan", bold=True))
        content.append(f"{job.location}\n", style=Style(color="grey85"))
        content.append(f"Status:   ", style=Style(color="bright_cyan", bold=True))
        content.append(f"{job.status}\n", style=Style(color="yellow"))

        if job.url:
            content.append(f"\nURL:      ", style=Style(color="bright_cyan", bold=True))
            content.append(f"{job.url}\n", style=Style(color="bright_blue", underline=True))

        if job.why:
            content.append(f"\nWhy You:  ", style=Style(color="bright_magenta", bold=True))
            # Wrap long text
            wrapped = textwrap.fill(job.why, width=60)
            content.append(f"{wrapped}\n", style=Style(color="grey85"))

        if job.how_to_apply:
            content.append(f"\nApply:    ", style=Style(color="bright_magenta", bold=True))
            wrapped = textwrap.fill(job.how_to_apply, width=60)
            content.append(f"{wrapped}\n", style=Style(color="grey85"))

        title = Text(f"📋 Job #{job.index} Details", style=Style(color="bright_cyan", bold=True))
        return Panel(
            content,
            title=title,
            border_style=Style(color="bright_magenta"),
            padding=(1, 2),
        )

    def build_action_bar(self) -> Panel:
        """Build the action menu bar."""
        if self.mode == "action":
            elements = []
            for i, (key, label) in enumerate(self.actions):
                if i == self.action_index:
                    style = Style(color="black", bgcolor="bright_cyan", bold=True)
                else:
                    style = Style(color="grey70")
                elements.append(Text(f" [{key}]{label} ", style=style))
            content = Text("  ").join(elements) if elements else Text("")
            border = Style(color="bright_cyan")
            title = Text("⚡ Actions (Enter=confirm, Esc=cancel)", style=Style(color="bright_cyan", bold=True))
        else:
            content = Text(
                " [G]enerate CV  [O]pen URL  [D]elete  [R]efresh  [Q]uit ",
                style=Style(color="grey50"),
                justify="center",
            )
            border = Style(color="grey42")
            title = Text("⚡ Actions", style=Style(color="grey50", bold=True))

        return Panel(
            content,
            title=title,
            border_style=border,
            padding=(0, 1),
        )

    def build_status_bar(self) -> Panel:
        """Build the status/message bar."""
        if self.message:
            msg_text = Text(f"  {self.message} ", style=self.message_style)
        else:
            msg_text = Text(
                f"  ↑↓ Navigate  ⏎ Actions  1-{len(self.jobs)} Jump  q Quit",
                style=Style(color="grey50"),
            )
        return Panel(
            msg_text,
            border_style=Style(color="grey30"),
            padding=(0, 1),
        )

    def build_header(self) -> Panel:
        """Build the dashboard header."""
        header_text = Text()
        header_text.append("🎯 ", style=Style(color="bright_cyan"))
        header_text.append("CURATED JOBS DASHBOARD", style=Style(color="bright_cyan", bold=True))
        header_text.append("  │  ", style=Style(color="grey42"))
        header_text.append(f"{len(self.jobs)} jobs", style=Style(color="white", bold=True))
        header_text.append("  │  ", style=Style(color="grey42"))
        header_text.append("Scout Feed", style=Style(color="bright_magenta"))

        return Panel(
            header_text,
            style=Style(bgcolor="rgb(20,20,40)"),
            border_style=Style(color="bright_cyan"),
            box=box.DOUBLE,
            padding=(0, 1),
        )

    def render(self) -> Table:
        """Render the full dashboard layout as a Rich group."""
        from rich.columns import Columns
        from rich.text import Text as RText

        layout_parts = []
        layout_parts.append(self.build_header())
        layout_parts.append(RText(""))
        layout_parts.append(self.build_table())
        layout_parts.append(RText(""))
        layout_parts.append(self.build_detail_panel())
        layout_parts.append(RText(""))
        layout_parts.append(self.build_action_bar())
        layout_parts.append(self.build_status_bar())

        return layout_parts

    def run_action(self, action_key: str):
        """Execute the selected action on the current job."""
        if not self.jobs:
            self.message = "No job selected"
            self.message_style = Style(color="yellow")
            return

        job = self.jobs[self.selected_index]

        if action_key == "G":
            self._generate_cv(job)
        elif action_key == "O":
            self._open_url(job)
        elif action_key == "D":
            self._delete_job(job)
        elif action_key == "R":
            self.refresh_jobs()

    def _generate_cv(self, job: Job):
        """Run the Terminal CV Generator with the job description."""
        if not os.path.exists(CV_GENERATOR_SCRIPT):
            self.message = f"CV Generator not found: {CV_GENERATOR_SCRIPT}"
            self.message_style = Style(color="red")
            return

        self.message = f"Generating CV for {job.company}..."
        self.message_style = Style(color="yellow")

        # Exit the live display before running subprocess
        print(f"\n{'='*60}")
        print(f"  Generating CV for: {job.company} — {job.role}")
        print(f"  Running: {CV_GENERATOR_SCRIPT}")
        print(f"{'='*60}\n")

        try:
            result = subprocess.run(
                ["bash", CV_GENERATOR_SCRIPT],
                input=job.description,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                self.message = f"CV generated for {job.company} ✓"
                self.message_style = Style(color="green")
            else:
                self.message = f"CV generator exited with code {result.returncode}"
                self.message_style = Style(color="red")
        except subprocess.TimeoutExpired:
            self.message = "CV generator timed out (5 min)"
            self.message_style = Style(color="red")
        except Exception as e:
            self.message = f"Error: {str(e)[:50]}"
            self.message_style = Style(color="red")

    def _open_url(self, job: Job):
        """Open the job URL in the default browser."""
        if not job.url:
            self.message = f"No URL found for {job.company}"
            self.message_style = Style(color="yellow")
            return

        try:
            # Try xdg-open on Linux
            subprocess.Popen(
                ["xdg-open", job.url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.message = f"Opened {job.url[:50]}..."
            self.message_style = Style(color="green")
        except FileNotFoundError:
            self.message = f"Browser not available. URL: {job.url[:40]}"
            self.message_style = Style(color="yellow")
        except Exception as e:
            self.message = f"Error opening URL: {str(e)[:40]}"
            self.message_style = Style(color="red")

    def _delete_job(self, job: Job):
        """Delete the job file from disk."""
        try:
            os.remove(job.filepath)
            self.message = f"Deleted {job.filename}"
            self.message_style = Style(color="green")
            self.refresh_jobs()
        except OSError as e:
            self.message = f"Error deleting: {str(e)[:40]}"
            self.message_style = Style(color="red")

    def handle_input(self, key: str) -> bool:
        """
        Handle a keyboard input. Returns False to quit.
        """
        if key == "q" or key == "Q" or key == "\x03":  # q or Ctrl+C
            return False

        if self.mode == "navigate":
            if key == "j" or key == "down":
                if self.jobs:
                    self.selected_index = (self.selected_index + 1) % len(self.jobs)
            elif key == "k" or key == "up":
                if self.jobs:
                    self.selected_index = (self.selected_index - 1) % len(self.jobs)
            elif key == "enter":
                if self.jobs:
                    self.mode = "action"
                    self.action_index = 0
                    self.message = "Select action"
                    self.message_style = Style(color="bright_cyan")
            elif key in self.action_keys:
                # Direct action shortcut
                self.run_action(key.upper())
            elif key == "r" or key == "R":
                self.refresh_jobs()
            elif key.isdigit():
                # Jump to job by number
                num = int(key)
                if self.jobs and 1 <= num <= len(self.jobs):
                    self.selected_index = num - 1
                    self.message = f"Selected job #{num}"
                    self.message_style = Style(color="bright_cyan")
        elif self.mode == "action":
            if key == "esc" or key == "\x1b":
                self.mode = "navigate"
                self.message = ""
            elif key == "h" or key == "left":
                self.action_index = (self.action_index - 1) % len(self.actions)
            elif key == "l" or key == "right":
                self.action_index = (self.action_index + 1) % len(self.actions)
            elif key == "enter":
                action_key = self.action_keys[self.action_index]
                self.run_action(action_key)
                self.mode = "navigate"
            elif key in self.action_keys:
                self.run_action(key.upper())
                self.mode = "navigate"

        return True

    def run(self):
        """Main loop using Rich Live display."""
        self.refresh_jobs()

        # Set terminal
        self.console.clear()

        # Use Live for real-time updates
        import sys
        import tty
        import termios
        import select

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())

            with Live(
                console=self.console,
                refresh_per_second=10,
                screen=True,
                transient=False,
            ) as live:
                # Initial render
                live.update(self._render_layout())

                while True:
                    # Check for input (non-blocking)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)

                        # Handle escape sequences (arrow keys)
                        if key == "\x1b":
                            # Try to read the rest of the escape sequence
                            if select.select([sys.stdin], [], [], 0.05)[0]:
                                seq = sys.stdin.read(2)
                                if seq == "[A":
                                    key = "up"
                                elif seq == "[B":
                                    key = "down"
                                elif seq == "[C":
                                    key = "right"
                                elif seq == "[D":
                                    key = "left"
                                elif seq == "\x1b":
                                    key = "esc"
                            else:
                                key = "esc"

                        if not self.handle_input(key):
                            break

                    # Re-render
                    live.update(self._render_layout())

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            self.console.clear()
            self.console.print(Text("Goodbye! 👋", style=Style(color="bright_cyan", bold=True)))

    def _render_layout(self):
        """Render all components as a list for Rich Live."""
        from rich.text import Text as RText

        parts = []
        parts.append(RText(""))
        parts.append(self.build_header())
        parts.append(RText(""))
        parts.append(self.build_table())
        parts.append(RText(""))
        parts.append(self.build_detail_panel())
        parts.append(RText(""))
        parts.append(self.build_action_bar())
        parts.append(self.build_status_bar())
        parts.append(RText(""))

        # Use a Column to stack everything
        from rich.console import Group
        return Group(*parts)

    def run_simple(self):
        """Simple non-TUI mode for desktop launchers. Renders once and waits for input."""
        self.refresh_jobs()
        self.console.clear()
        self.console.print(self._render_layout())
        self.console.print("\n")
        self.console.print("[bold yellow]Commands:[/bold yellow] [G#]enerate CV  [O#]pen URL  [D#]elete  [R]efresh  [Q]uit")
        self.console.print("[dim]Example: G1 = Generate CV for job #1, O3 = Open URL for job #3[/dim]\n")

        while True:
            try:
                line = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if not line:
                continue

            if line == "q" or line == "quit":
                break
            elif line == "r" or line == "refresh":
                self.refresh_jobs()
                self.console.clear()
                self.console.print(self._render_layout())
            elif line.startswith("g") and line[1:].isdigit():
                num = int(line[1:])
                for job in self.jobs:
                    if job.index == num:
                        self._generate_cv(job)
                        break
                else:
                    self.console.print(f"[red]Job #{num} not found[/red]")
            elif line.startswith("o") and line[1:].isdigit():
                num = int(line[1:])
                for job in self.jobs:
                    if job.index == num:
                        self._open_url(job)
                        break
                else:
                    self.console.print(f"[red]Job #{num} not found[/red]")
            elif line.startswith("d") and line[1:].isdigit():
                num = int(line[1:])
                for job in self.jobs:
                    if job.index == num:
                        self._delete_job(job)
                        break
                else:
                    self.console.print(f"[red]Job #{num} not found[/red]")
            else:
                self.console.print(f"[red]Unknown command: {line}[/red]")
                self.console.print("[dim]Use: G1, O1, D1, R, Q[/dim]")


# ── Entry Point ────────────────────────────────────────────────────────────────
def main():
    """Entry point for the dashboard."""
    # Handle SIGINT gracefully
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    dashboard = JobsDashboard()

    # Check if we're in an interactive terminal
    if sys.stdin.isatty():
        # Full TUI mode
        dashboard.run()
    else:
        # Simple mode for desktop launchers (non-tty)
        dashboard.run_simple()


if __name__ == "__main__":
    main()
