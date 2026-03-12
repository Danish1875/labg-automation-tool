"""
Soft-warn structure validator for generated CloudLabs Markdown files.

Two completely separate validation paths:
  - validate_get_started()   → checks getStarted.md structure
  - validate_lab_exercise()  → checks Lab01.md, Lab02.md structure

The top-level validate() function routes to the correct path automatically
based on the page_type passed in from app.py.

SOFT-WARN MODE: Warnings are printed but never block output from being saved.
Think of this as a linter, not a gatekeeper.
"""

import re

# ─── Shared helpers ────────────────────────────────────────────────────────────

def _heading_present(content: str, heading: str, level: str = None) -> bool:
    """
    Check if a heading exists in the markdown content.
    level: "#", "##", "###" — if None, matches any heading level.
    """
    if level:
        pattern = rf"^{re.escape(level)}\s+{re.escape(heading)}"
    else:
        pattern = rf"^#+\s+{re.escape(heading)}"
    return bool(re.search(pattern, content, re.IGNORECASE | re.MULTILINE))


def _heading_position(content: str, heading: str) -> int:
    """Return the character position of a heading, or -1 if not found."""
    match = re.search(rf"^#+\s+{re.escape(heading)}", content, re.IGNORECASE | re.MULTILINE)
    return match.start() if match else -1


def _check_section_order(content: str, required_order: list, warnings: list) -> list:
    """Verify sections appear in the expected order."""
    positions = {}
    for section in required_order:
        pos = _heading_position(content, section)
        if pos != -1:
            positions[section] = pos

    found_ordered = sorted(positions.items(), key=lambda x: x[1])
    found_names = [name for name, _ in found_ordered]
    expected_names = [s for s in required_order if s in positions]

    if found_names != expected_names:
        warnings.append(
            f"⚠️  Section order mismatch.\n"
            f"     Expected : {expected_names}\n"
            f"     Found    : {found_names}"
        )
    return warnings


def _check_code_block_languages(content: str, warnings: list) -> list:
    """Ensure all code blocks use only allowed languages."""
    allowed = {"bash", "powershell", "azurecli", "json", "python", "c#"}
    found_langs = re.findall(r"```(\w+)", content)
    for lang in found_langs:
        if lang.lower() not in allowed:
            warnings.append(
                f"⚠️  Code block uses unlisted language: `{lang}`\n"
                f"     Allowed: {', '.join(sorted(allowed))}"
            )
    return warnings


def _check_image_paths(content: str, warnings: list) -> list:
    """Ensure image paths follow the ../media/ convention."""
    images = re.findall(r"!\[.*?\]\((.*?)\)", content)
    for path in images:
        if path and not path.startswith("../media/"):
            warnings.append(
                f"⚠️  Image path may be incorrect: `{path}`\n"
                f"     Expected format: ../media/filename.png"
            )
    return warnings


# ─── GET STARTED validator ─────────────────────────────────────────────────────

# Sections AI must generate (in order)
GS_AI_SECTIONS = [
    "Overview",
    "Objectives",
    "Pre-requisites",
    "Architecture",
    "Architecture Diagram",
    "Explanation of Components",
]

# Sections that must be copied verbatim from the template
GS_STATIC_SECTIONS = [
    "Getting Started with Lab",
    "Accessing Your Lab Environment",
    "Lab Guide Zoom In/Zoom Out",
    "Virtual Machine & Lab Guide",
    "Exploring Your Lab Resources",
    "Utilizing the Split Window Feature",
    "Managing Your Virtual Machine",
    "Let's Get Started with Azure Portal",
    "Support Contact",
]


def validate_get_started(content: str) -> bool:
    """
    Validate a getStarted.md file.
    Checks:
      1. All AI-generated sections present and in order
      2. All static boilerplate sections present
      3. Architecture Diagram section contains an image reference
      4. No <validation step> tags (wrong page type)
      5. No ## Task headings (wrong page type)
      6. Image paths follow ../media/ convention
    """
    print("\n[Validator] 🔍 Running getStarted.md validation...\n")
    warnings = []

    # 1. Check AI-generated sections
    for section in GS_AI_SECTIONS:
        if not _heading_present(content, section):
            warnings.append(f"⚠️  Missing AI-generated section: '{section}'")

    # Check order of AI sections
    warnings = _check_section_order(content, GS_AI_SECTIONS, warnings)

    # 2. Check static boilerplate sections
    for section in GS_STATIC_SECTIONS:
        if not _heading_present(content, section):
            warnings.append(f"⚠️  Missing static boilerplate section: '{section}'")

    # Static sections should appear after AI sections
    last_ai_pos = max(
        (_heading_position(content, s) for s in GS_AI_SECTIONS if _heading_position(content, s) != -1),
        default=-1
    )
    for section in GS_STATIC_SECTIONS:
        pos = _heading_position(content, section)
        if pos != -1 and pos < last_ai_pos:
            warnings.append(
                f"⚠️  Static section '{section}' appears before AI-generated sections.\n"
                f"     Static boilerplate must come after '## Explanation of Components'."
            )

    # 3. Architecture Diagram must have an image
    arch_match = re.search(r"## Architecture Diagram(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if arch_match:
        arch_block = arch_match.group(1)
        if not re.search(r"!\[.*?\]\(.*?\)", arch_block):
            warnings.append(
                "⚠️  ## Architecture Diagram section has no image reference.\n"
                "     Expected: ![](../media/architecture.png)"
            )

    # 4. No validation GUID tags (these belong in lab_exercise pages)
    if re.search(r'<validation\s+step=', content):
        warnings.append(
            "⚠️  <validation step> tag found in getStarted.md.\n"
            "     Validation blocks belong in lab exercise pages only."
        )

    # 5. No Task headings
    if re.search(r"^##\s+Task\s+\d+", content, re.IGNORECASE | re.MULTILINE):
        warnings.append(
            "⚠️  Task heading found in getStarted.md.\n"
            "     Tasks belong in lab exercise pages (Lab01.md, Lab02.md) only."
        )

    # 6. Image paths
    warnings = _check_image_paths(content, warnings)

    return _print_results(warnings, "getStarted.md")


# ─── LAB EXERCISE validator ────────────────────────────────────────────────────

LAB_REQUIRED_ORDER = [
    "Lab Overview",
    "Lab Objectives",
]


def validate_lab_exercise(content: str) -> bool:
    """
    Validate a Lab exercise Markdown file (Lab01.md, Lab02.md, etc.).
    Checks:
      1. Lab Overview and Lab Objectives present and in order
      2. At least one ## Task N: heading exists
      3. Each Task has a <validation step> block after it
      4. ## Summary section present at end
      5. Numbered steps exist
      6. Code blocks use only allowed languages
      7. No architecture/get-started-only sections leaked in
      8. Image paths follow ../media/ convention
    """
    print("\n[Validator] 🔍 Running lab exercise validation...\n")
    warnings = []

    # 1. Required top-level sections
    for section in LAB_REQUIRED_ORDER:
        if not _heading_present(content, section):
            warnings.append(f"⚠️  Missing required section: '{section}'")

    warnings = _check_section_order(content, LAB_REQUIRED_ORDER, warnings)

    # 2. At least one Task heading
    tasks = re.findall(r"^##\s+Task\s+(\d+)\s*:", content, re.IGNORECASE | re.MULTILINE)
    if not tasks:
        warnings.append(
            "⚠️  No Task headings found.\n"
            "     Expected format: ## Task 1: Descriptive Title"
        )

    # 3. Validation block after each task
    task_blocks = list(re.finditer(r"^##\s+Task\s+\d+\s*:.*$", content, re.IGNORECASE | re.MULTILINE))
    for i, task_match in enumerate(task_blocks):
        task_start = task_match.start()
        # Next task or end of file
        task_end = task_blocks[i + 1].start() if i + 1 < len(task_blocks) else len(content)
        task_block_content = content[task_start:task_end]
        task_title = task_match.group().strip()

        if not re.search(r'<validation\s+step="[^"]*"\s*/>', task_block_content):
            warnings.append(
                f"⚠️  No <validation step=\"...\"> block found after:\n"
                f"     {task_title}\n"
                f"     Add: <validation step=\"placeholder-guid-task{i+1}\" />"
            )

    # 4. Summary section
    if not _heading_present(content, "Summary"):
        warnings.append(
            "⚠️  Missing ## Summary section.\n"
            "     Add a summary at the end describing what was accomplished."
        )

    # 5. Numbered steps
    if not re.findall(r"^\d+\.\s+\S+", content, re.MULTILINE):
        warnings.append("⚠️  No numbered steps found. Steps must use '1. 2. 3.' format.")

    # 6. Code block languages
    warnings = _check_code_block_languages(content, warnings)

    # 7. No get-started-only sections leaked in
    for bad_section in ["Architecture Diagram", "Explanation of Components", "Support Contact"]:
        if _heading_present(content, bad_section):
            warnings.append(
                f"⚠️  Section '{bad_section}' found in lab exercise file.\n"
                f"     This section belongs in getStarted.md only."
            )

    # 8. Image paths
    warnings = _check_image_paths(content, warnings)

    return _print_results(warnings, "lab exercise")


# ─── Result printer ────────────────────────────────────────────────────────────

def _print_results(warnings: list, page_label: str) -> bool:
    if warnings:
        print(f"[Validator] ⚠️  {len(warnings)} warning(s) for {page_label} — output saved anyway:\n")
        for w in warnings:
            print(f"  {w}\n")
        return False
    else:
        print(f"[Validator] ✅ All checks passed for {page_label}!\n")
        return True


# ─── Main entry point ──────────────────────────────────────────────────────────

def validate(markdown_content: str, yaml_rules: dict, page_type: str) -> bool:
    """
    Route to the correct validator based on page_type.

    Args:
        markdown_content: The full generated markdown string
        yaml_rules:       Parsed labStructure.yaml dict (passed for future extensibility)
        page_type:        "get_started" or "lab_exercise"

    Returns:
        True if no warnings, False if warnings exist (output still saved either way)
    """
    if page_type == "get_started":
        return validate_get_started(markdown_content)
    elif page_type == "lab_exercise":
        return validate_lab_exercise(markdown_content)
    else:
        print(f"[Validator] ⚠️  Unknown page_type: '{page_type}' — skipping validation.")
        return False