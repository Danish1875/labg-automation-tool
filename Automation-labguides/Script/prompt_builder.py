"""
Constructs system + user prompts for Azure OpenAI based on PAGE TYPE.

Two distinct prompt paths:
  - get_started    → getStarted.md  (Overview → Architecture → static boilerplate)
  - lab_exercise   → LabN.md        (Lab Overview → Objectives → Tasks → Summary)

The page type is detected from the prompt text written in Inputs/prompts.txt.
Authors signal the page type using the PAGE_TYPE placeholder (see prompts.txt template).
"""

import json
import re


# ─── Page type detection ───────────────────────────────────────────────────────

def detect_page_type(prompt_text: str) -> str:
    """
    Detect whether the prompt is for a getStarted page or a lab exercise page.

    Authors set this explicitly in prompts.txt using:
        PAGE_TYPE: get_started
        PAGE_TYPE: lab_exercise

    Falls back to keyword inference if not set.
    Returns: "get_started" or "lab_exercise"
    """
    # Explicit declaration (preferred)
    match = re.search(r"PAGE_TYPE\s*:\s*(get_started|lab_exercise)", prompt_text, re.IGNORECASE)
    if match:
        page_type = match.group(1).lower()
        print(f"[Prompt Builder] ✅ Page type detected (explicit): {page_type}")
        return page_type

    # Keyword fallback
    lower = prompt_text.lower()
    if any(kw in lower for kw in ["get started", "getting started", "overview page", "lab environment", "architecture diagram"]):
        print("[Prompt Builder] ✅ Page type detected (inferred): get_started")
        return "get_started"

    print("[Prompt Builder] ✅ Page type detected (inferred): lab_exercise")
    return "lab_exercise"


# ─── System prompt ─────────────────────────────────────────────────────────────

def build_system_prompt(yaml_rules: dict, page_type: str) -> str:
    """
    Build the system prompt for the given page type.
    Embeds the relevant YAML rules section so the model treats them as hard constraints.
    """

    # Extract only the relevant rule section + shared rules
    relevant_rules = {
        "page_type": page_type,
        page_type: yaml_rules.get(page_type, {}),
        "shared": yaml_rules.get("shared", {}),
        "lab_metadata": yaml_rules.get("lab_metadata", {})
    }
    rules_str = json.dumps(relevant_rules, indent=2)

    if page_type == "get_started":
        page_context = _get_started_system_context()
    else:
        page_context = _lab_exercise_system_context()

    system_prompt = f"""
You are an expert technical writer for CloudLabs by Spektra Systems.
Your job is to generate professional, structured lab guides in Markdown format
rendered on the CloudLabs learning platform for cloud learners.

────────────────────────────────────────────
PLATFORM CONTEXT
────────────────────────────────────────────
- Each lab is a series of Markdown files served in order on CloudLabs.
- File order: getStarted.md → Lab01.md → Lab02.md → ...
- You are generating ONE file. Be complete. Do not truncate.
- Output ONLY valid Markdown. No preamble, no explanation, no code fences wrapping the whole file.
- Start directly with the # heading.

────────────────────────────────────────────
PAGE-SPECIFIC INSTRUCTIONS
────────────────────────────────────────────
{page_context}

────────────────────────────────────────────
STRUCTURE RULES (from labStructure.yaml — enforce strictly)
────────────────────────────────────────────
{rules_str}

────────────────────────────────────────────
CLOUDLABS STYLE GUIDE (apply to all pages)
────────────────────────────────────────────
- **Bold** every UI element the user must click (e.g., **+ Create**, **Save**, **Next**)
- `inline code` for values users must type into fields
- > **Note:** for callouts and warnings
- > **Congratulations** blocks after major task completions (lab_exercise only)
- Images referenced inline within the step they relate to: ![](../media/filename.png)
- Use <inject key="DeploymentID" enableCopy="false"></inject> for dynamic environment values
- Use <inject key="Region" enableCopy="false"></inject> for region values
- Use <inject key="AzureAdUserEmail"></inject> for user email
- Use <inject key="AzureAdUserPassword"></inject> for user password
""".strip()

    return system_prompt


def _get_started_system_context() -> str:
    return """
You are generating a getStarted.md page — the FIRST page of a CloudLabs lab.
This page has TWO parts:

PART 1 — AI GENERATED (you write this based on the lab description):
  These sections must appear in EXACTLY this order:
    1.  # <Lab Title>
    2.  ### Overall Estimated Duration: X hours
    3.  ## Overview
    4.  ## Objectives
    5.  ## Pre-requisites
    6.  ## Architecture
    7.  ## Architecture Diagram
            → Insert: ![](../media/architecture.png)
            → Add a one-line caption below describing what the diagram shows
    8.  ## Explanation of Components
            → Use bullet points: **Component Name:** one-line description

PART 2 — STATIC BOILERPLATE (copy verbatim from the reference template):
  After Explanation of Components, append the following sections EXACTLY
  as they appear in the reference template. Do NOT rewrite or paraphrase them:
    - ## Getting Started with Lab
    - ## Accessing Your Lab Environment
    - ## Lab Guide Zoom In/Zoom Out
    - ## Virtual Machine & Lab Guide
    - ## Exploring Your Lab Resources
    - ## Utilizing the Split Window Feature
    - ## Managing Your Virtual Machine
    - ## Let's Get Started with Azure Portal
    - ## Support Contact

  These sections contain platform UI instructions that must be identical
  across all labs. Copy image references and inject keys exactly as shown.
""".strip()


def _lab_exercise_system_context() -> str:
    return """
You are generating a Lab exercise page (e.g., Lab01.md, Lab02.md).
This page contains the hands-on technical tasks for learners.

REQUIRED STRUCTURE (in this exact order):
    1.  # Lab 0N: <Lab Title from prompt>
    2.  ### Estimated Duration: X Minutes
    3.  ## Lab Overview
            → 2-3 sentences describing what this lab covers
    4.  ## Lab Objectives
            → Brief intro sentence, then bullet list of tasks:
            - Task 1: <title>
            - Task 2: <title>
            - Task 3: <title>  (as many as defined in the prompt)
    5.  ## Task 1: <Descriptive Title>
        → Intro sentence explaining the task goal
        → Numbered steps (1. 2. 3.)
        → Each step that involves a CLI command MUST have a code block
        → Screenshots referenced inline: ![](../media/step-description.png)
        → End with:
            <validation step="placeholder-guid-task1" />
            > **Congratulations** on completing the task! ...
    6.  ## Task 2: <Descriptive Title>  (repeat pattern)
    ...
    N.  ## Summary
            → 2-3 sentences summarising what was accomplished
            → ### Congratulations on completing the lab!

STEP WRITING RULES:
  - Every step title must be descriptive (not just "Step 1")
  - Bold ALL UI elements: **Resource groups**, **+ Create**, **Save**
  - Use `inline code` for names/values users type: `my-storage-account`
  - Note blocks: > **Note:** text here
  - Sub-bullets under a step use standard markdown indentation
""".strip()


# ─── User prompt ───────────────────────────────────────────────────────────────

def build_user_prompt(
    user_prompt: str,
    template_content: str,
    template_name: str,
    page_type: str,
    screenshot_context: list = None
) -> str:
    """
    Build the user-facing prompt with lab description, template reference,
    and screenshot context (Phase 2).
    """
    screenshot_context = screenshot_context or []

    # Build screenshot section
    if screenshot_context:
        screenshot_section = (
            "────────────────────────────────────────────\n"
            "SCREENSHOT CONTEXT (use to sequence steps accurately)\n"
            "────────────────────────────────────────────\n"
        )
        for item in screenshot_context:
            screenshot_section += (
                f"Step {item['step_number']} — {item['filename']}:\n"
                f"{item['description']}\n\n"
            )
        screenshot_section += (
            "Instructions:\n"
            "  1. Follow the screenshot order to sequence steps correctly\n"
            "  2. Embed each screenshot inline at the step it belongs to: ![](../media/filename.png)\n"
            "  3. Match all UI element names exactly as described\n"
        )
    else:
        screenshot_section = (
            "────────────────────────────────────────────\n"
            "SCREENSHOT CONTEXT\n"
            "────────────────────────────────────────────\n"
            "No screenshots provided for this run.\n"
            "Insert placeholder image references where screenshots logically belong:\n"
            "  ![](../media/descriptive-step-name.png)\n"
            "These will be replaced with real screenshots in Phase 2.\n"
        )

    if page_type == "get_started":
        page_instruction = (
            "────────────────────────────────────────────\n"
            "OUTPUT INSTRUCTIONS\n"
            "────────────────────────────────────────────\n"
            "Generate a getStarted.md file.\n\n"
            "PART 1 — Write these sections using the lab description below:\n"
            "  # Title, ### Duration, ## Overview, ## Objectives, ## Pre-requisites,\n"
            "  ## Architecture, ## Architecture Diagram, ## Explanation of Components\n\n"
            "PART 2 — Copy these sections VERBATIM from the reference template:\n"
            "  ## Getting Started with Lab → ## Support Contact\n"
            "  Do not paraphrase or rewrite them. Copy image paths and inject keys exactly.\n"
        )
    else:
        page_instruction = (
            "────────────────────────────────────────────\n"
            "OUTPUT INSTRUCTIONS\n"
            "────────────────────────────────────────────\n"
            "Generate a Lab exercise Markdown file (e.g., Lab01.md).\n"
            "Follow the required structure: Lab Overview → Lab Objectives → Tasks → Summary.\n"
            "Each Task ends with a <validation step=\"placeholder-guid-taskN\" /> block.\n"
            "The final section must be ## Summary.\n"
        )

    user_prompt_full = f"""
Generate a complete CloudLabs lab guide Markdown file based on the following inputs.

────────────────────────────────────────────
LAB DESCRIPTION (from prompts.txt)
────────────────────────────────────────────
{user_prompt}

────────────────────────────────────────────
REFERENCE TEMPLATE ({template_name})
────────────────────────────────────────────
Use this as your structural and stylistic reference.
Mirror heading levels, callout styles, inject-key patterns, and image path formats.
Do NOT copy the lab-specific content — generate fresh content from the description above.

{template_content}

{screenshot_section}

{page_instruction}
Output only the Markdown. Nothing else.
""".strip()

    return user_prompt_full