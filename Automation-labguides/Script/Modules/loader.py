"""
loader.py
---------
Reads all inputs needed for lab guide generation:
  - Inputs/prompts.txt          → user's lab description
  - Templates/*.md              → reference template
  - Rules/labStructure.yaml     → validation rules
  - Screenshot/                 → images (stubbed, ready for Phase 2)
"""

import os
import yaml


def get_repo_root() -> str:
    """
    Navigate from Script/Modules/ up two levels to reach Automation-labguides/ root.
    All sibling folders (Inputs, Templates, Rules, etc.) live there.
    """
    modules_dir = os.path.dirname(os.path.abspath(__file__))  # .../Script/Modules/
    script_dir  = os.path.dirname(modules_dir)                # .../Script/
    return os.path.dirname(script_dir)                        # .../Automation-labguides/


def load_prompt(filename: str = "prompts.txt") -> str:
    """
    Load the lab description prompt from Inputs/prompts.txt.
    Raises clearly if the file is missing or empty.
    """
    root = get_repo_root()
    path = os.path.join(root, "Inputs", filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"[Loader] ❌ prompts.txt not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(
            "[Loader] ❌ prompts.txt is empty.\n"
            "Please describe your lab in detail — include objectives, "
            "steps, Azure services used, and any commands required."
        )

    print(f"[Loader] ✅ Prompt loaded ({len(content)} chars)")
    return content


def load_template(template_name: str = None) -> tuple:
    """
    Load a markdown template from Templates/.
    - If template_name is provided, loads that specific file.
    - Otherwise, auto-selects the first .md file found.
    Returns (template_content: str, template_filename: str)
    """
    root = get_repo_root()
    templates_dir = os.path.join(root, "Templates")

    if template_name:
        path = os.path.join(templates_dir, template_name)
    else:
        md_files = sorted([f for f in os.listdir(templates_dir) if f.endswith(".md")])
        if not md_files:
            raise FileNotFoundError(f"[Loader] ❌ No .md templates found in: {templates_dir}")
        template_name = md_files[0]
        path = os.path.join(templates_dir, template_name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"[Loader] ❌ Template not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    print(f"[Loader] ✅ Template loaded: {template_name}")
    return content, template_name


def load_yaml_rules(filename: str = "labStructure.yaml") -> dict:
    """
    Load and parse the YAML structure rules from Rules/.
    These rules are injected into the AI prompt as formatting constraints.
    """
    root = get_repo_root()
    path = os.path.join(root, "Rules", filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"[Loader] ❌ labStructure.yaml not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    print(f"[Loader] ✅ YAML rules loaded: {filename}")
    return rules


def load_screenshots(prompt_text: str = "") -> list:
    """
    Scans Screenshot/<lab_folder>/ for images.
    The folder name is read from SCREENSHOT_FOLDER in prompts.txt.

    Returns sorted list of absolute image paths.
    Returns [] if no folder specified or folder is empty.
    """
    import re as _re

    # Read SCREENSHOT_FOLDER from prompt
    match = _re.search(r"SCREENSHOT_FOLDER\s*:\s*(\S+)", prompt_text, _re.IGNORECASE)
    if not match:
        print("[Loader] 📸 No SCREENSHOT_FOLDER defined in prompts.txt — skipping screenshots.")
        return []

    lab_folder = match.group(1).strip()
    root       = get_repo_root()
    folder_path = os.path.join(root, "Screenshot", lab_folder)

    if not os.path.exists(folder_path):
        print(f"[Loader] 📸 Screenshot folder not found: Screenshot/{lab_folder}/ — skipping.")
        return []

    valid_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    files = sorted([
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in valid_exts
    ])

    if files:
        print(f"[Loader] 📸 {len(files)} screenshot(s) found in Screenshot/{lab_folder}/")
    else:
        print(f"[Loader] 📸 Screenshot/{lab_folder}/ is empty — skipping image analysis.")

    return files