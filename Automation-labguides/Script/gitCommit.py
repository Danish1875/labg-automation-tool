"""
gitCommit.py
------------
Stages the generated lab guide file to git (local only — no push).

Workflow:
  1. git add <file>           → stages the specific output file
  2. git status               → shows what's staged for review
  3. Prints a reminder to commit manually when ready

This keeps the author in control of the commit message and push timing.
Auto-push will be added in a future iteration.
"""

import subprocess
import os
import sys


def get_repo_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def _run(cmd: list, cwd: str) -> tuple:
    """Run a shell command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def stage_file(file_path: str) -> bool:
    """
    Stage a specific file with `git add`.

    Args:
        file_path: Absolute path to the file to stage.

    Returns:
        True if staging succeeded, False otherwise.
    """
    root = get_repo_root()

    if not os.path.exists(file_path):
        print(f"[Git] ❌ File not found, cannot stage: {file_path}")
        return False

    # Make path relative to repo root for cleaner git output
    try:
        rel_path = os.path.relpath(file_path, root)
    except ValueError:
        rel_path = file_path

    print(f"\n[Git] 📁 Staging file: {rel_path}")

    stdout, stderr, code = _run(["git", "add", file_path], cwd=root)

    if code != 0:
        print(f"[Git] ❌ git add failed:\n  {stderr}")
        return False

    print(f"[Git] ✅ File staged successfully.")

    # Show git status so the author can see what's ready
    print("\n[Git] 📋 Current staging area (git status):")
    stdout, stderr, code = _run(["git", "status", "--short"], cwd=root)
    if stdout:
        print(f"  {stdout}")
    else:
        print("  (nothing additional to show)")

    print(
        "\n[Git] 💡 To commit, run:\n"
        f'       git commit -m "Add generated lab guide: {os.path.basename(file_path)}"\n'
        f"       git push origin <your-branch-name>\n"
    )

    return True


# ─── Called directly for manual staging ───────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gitCommit.py <path-to-file>")
        print("Example: python gitCommit.py ../Labs-output/Lab1.md")
        sys.exit(1)

    target = os.path.abspath(sys.argv[1])
    success = stage_file(target)
    sys.exit(0 if success else 1)