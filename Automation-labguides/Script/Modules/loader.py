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
    Navigate from Script/ up one level to reach Automation-labguides/ root.
    All sibling folders (Inputs, Templates, Rules, etc.) live here.
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


def load_screenshots() -> list:
    """
    PHASE 2 STUB — Screenshot analysis not yet implemented.

    When active, this will:
      1. Scan Screenshot/ for .png files
      2. Sort them by filename (numeric order matches click sequence)
      3. Pass each image to image_analyzer.py for Azure Vision / GPT-4o analysis
      4. Return ordered list of { filename, description, step_number }

    For now, returns an empty list so the pipeline continues unaffected.
    """
    root = get_repo_root()
    screenshot_dir = os.path.join(root, "Screenshot")

    png_files = sorted([
        f for f in os.listdir(screenshot_dir)
        if f.lower().endswith(".png")
    ])

    if png_files:
        print(f"[Loader] 📸 {len(png_files)} screenshot(s) found — image analysis coming in Phase 2.")
        print(f"         Files detected: {png_files}")
    else:
        print("[Loader] 📸 No screenshots found in Screenshot/ — skipping image analysis.")

    # Returns empty list — image_analyzer.py will populate this in Phase 2
    return []