"""
output_writer.py
----------------
Saves the generated Markdown lab guide to Labs-output/.

Handles:
  - Auto-naming: detects if output is a getStarted or Lab file
  - Incrementing lab number (Lab1.md, Lab2.md, ...) if multiple labs exist
  - Never overwrites existing files — bumps the number instead
  - Returns the final saved path so gitCommit.py knows what to stage
"""

import os
import re


def get_repo_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def _detect_file_type(markdown_content: str, prompt_text: str) -> str:
    """
    Determine whether to name the output getStarted.md or LabN.md.

    Checks:
      1. If the markdown title or content mentions 'get started' / 'welcome' / 'overview'
      2. If the prompt mentions it's an intro or getting started page
    """
    combined = (markdown_content[:500] + prompt_text).lower()

    if any(kw in combined for kw in ["get started", "getting started", "welcome to", "overview", "lab environment"]):
        return "getStarted"
    return "lab"


def _next_lab_filename(output_dir: str, file_type: str) -> str:
    """
    Determine the next available filename in Labs-output/.

    - getStarted type → always getStarted.md (warns if exists)
    - lab type        → Lab1.md, Lab2.md, Lab3.md ... (auto-increments)
    """
    if file_type == "getStarted":
        candidate = os.path.join(output_dir, "getStarted.md")
        if os.path.exists(candidate):
            print("[Output Writer] ⚠️  getStarted.md already exists — will overwrite.")
        return "getStarted.md"

    # Find highest existing LabN.md and increment
    existing = [
        f for f in os.listdir(output_dir)
        if re.match(r"Lab\d+\.md", f, re.IGNORECASE)
    ]

    if not existing:
        return "Lab1.md"

    numbers = [int(re.search(r"\d+", f).group()) for f in existing]
    next_num = max(numbers) + 1
    return f"Lab{next_num}.md"


def save(markdown_content: str, prompt_text: str = "", filename: str = None) -> str:
    """
    Save the generated markdown to Labs-output/.

    Args:
        markdown_content: The full generated .md content
        prompt_text:      The original prompt (used for file type detection)
        filename:         Optional override (e.g., "Lab2.md"). If None, auto-named.

    Returns:
        The absolute path of the saved file.
    """
    root = get_repo_root()
    output_dir = os.path.join(root, "Labs-output")
    os.makedirs(output_dir, exist_ok=True)

    if filename:
        final_name = filename
    else:
        file_type = _detect_file_type(markdown_content, prompt_text)
        final_name = _next_lab_filename(output_dir, file_type)

    full_path = os.path.join(output_dir, final_name)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"[Output Writer] ✅ Lab guide saved: Labs-output/{final_name}")
    print(f"[Output Writer]    Full path: {full_path}")
    return full_path