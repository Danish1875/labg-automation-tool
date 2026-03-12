"""
output_writer.py
----------------
Saves the generated Markdown lab guide to Labs-output/.

File naming is driven by PAGE_TYPE read directly from prompts.txt —
never guessed from content. This prevents mismatches like a storage
account lab being saved as getStarted.md.

Output structure in Labs-output/:
    Labs-output/
        getStarted.md          ← always at root level (one per lab series)
        Lab01/
            Lab01.md
        Lab02/
            Lab02.md
        ...

The subfolder per lab keeps assets, screenshots, and the md file
together when the lab grows, and avoids filename collisions.
"""

import os
import re


def get_repo_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(script_dir)


def _read_page_type(prompt_text: str) -> str:
    """
    Read PAGE_TYPE directly from the raw prompt string.
    This is the single source of truth — never inferred from content.
    Returns 'get_started' or 'lab_exercise'.
    """
    match = re.search(r"PAGE_TYPE\s*:\s*(get_started|lab_exercise)", prompt_text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return "lab_exercise"  # safe default


def _read_lab_number(prompt_text: str) -> str:
    """
    Read LAB_NUMBER from prompt. Returns zero-padded string e.g. '01', '02'.
    Falls back to auto-incrementing if not set.
    """
    match = re.search(r"LAB_NUMBER\s*:\s*(\d+)", prompt_text, re.IGNORECASE)
    if match:
        return match.group(1).zfill(2)
    return None


def _next_lab_number(output_dir: str) -> str:
    """
    Auto-increment lab number based on existing Lab## folders in Labs-output/.
    Returns zero-padded string e.g. '01', '02', '03'.
    """
    existing = [
        d for d in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, d))
        and re.match(r"Lab\d+", d, re.IGNORECASE)
    ]
    if not existing:
        return "01"
    numbers = [int(re.search(r"\d+", d).group()) for d in existing]
    return str(max(numbers) + 1).zfill(2)


def save(markdown_content: str, prompt_text: str = "", filename: str = None) -> str:
    """
    Save the generated markdown to Labs-output/.

    Routing logic:
      PAGE_TYPE: get_started  → Labs-output/getStarted.md  (root level)
      PAGE_TYPE: lab_exercise → Labs-output/Lab01/Lab01.md  (subfolder)

    Args:
        markdown_content : Full generated .md string
        prompt_text      : Raw prompts.txt content (used to read PAGE_TYPE + LAB_NUMBER)
        filename         : Optional full filename override (e.g. 'Lab02.md')

    Returns:
        Absolute path of the saved file.
    """
    root = get_repo_root()
    output_dir = os.path.join(root, "Labs-output")
    os.makedirs(output_dir, exist_ok=True)

    page_type = _read_page_type(prompt_text)

    # ── getStarted.md → root of Labs-output/ ──────────────────────────────────
    if page_type == "get_started":
        final_name = filename or "getStarted.md"
        full_path = os.path.join(output_dir, final_name)

        if os.path.exists(full_path):
            print(f"[Output Writer] ⚠️  {final_name} already exists — overwriting.")

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"[Output Writer] ✅ Saved: Labs-output/{final_name}")
        return full_path

    # ── Lab exercise → Labs-output/Lab##/Lab##.md ──────────────────────────────
    if filename:
        # Override provided — extract number from it or use as-is
        num_match = re.search(r"\d+", filename)
        lab_num = num_match.group().zfill(2) if num_match else "01"
        final_name = filename if filename.endswith(".md") else f"{filename}.md"
    else:
        lab_num = _read_lab_number(prompt_text) or _next_lab_number(output_dir)
        final_name = f"Lab{lab_num}.md"

    # Create subfolder Labs-output/Lab##/
    lab_folder = os.path.join(output_dir, f"Lab{lab_num}")
    os.makedirs(lab_folder, exist_ok=True)

    full_path = os.path.join(lab_folder, final_name)

    if os.path.exists(full_path):
        print(f"[Output Writer] ⚠️  {final_name} already exists in Lab{lab_num}/ — overwriting.")

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"[Output Writer] ✅ Saved: Labs-output/Lab{lab_num}/{final_name}")
    return full_path