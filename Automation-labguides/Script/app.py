"""
app.py
------
Main entry point for the AI-Powered Lab Guide Generator.
Run from the Script/ directory:

    python app.py

Optional arguments:
    --template   <filename>           Specify a template file from Templates/
    --output     <filename>           Override the output filename in Labs-output/
    --page-type  get_started|lab_exercise   Override page type detection
    --no-commit                       Skip git staging step

Pipeline:
    1. Load inputs         (loader.py)
    2. Detect page type    (prompt_builder.py)
    3. Analyze images      (image_analyzer.py)   ← Phase 2 stub
    4. Fetch MS Learn docs   (ms_learn.py)        ← Phase 2 enhancement
    5. Build prompts       (prompt_builder.py)
    6. Call Azure OpenAI   (ai_client.py)
    7. Validate output     (validator.py)         ← routes to correct validator
    8. Save to disk        (output_writer.py)
    9. Stage with git      (gitCommit.py)
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import loader
import prompt_builder
import ai_client
import validator
import output_writer
import image_analyzer
import gitCommit
import ms_learn


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-Powered CloudLabs Lab Guide Generator",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--template",
        type=str,
        default=None,
        help=(
            "Template filename from Templates/\n"
            "  get_started  → use getstarted.md\n"
            "  lab_exercise → use azureaiTemplate.md\n"
            "Default: auto-selects based on page type"
        )
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output filename override (e.g. Lab01.md)\nDefault: auto-named"
    )
    parser.add_argument(
        "--page-type",
        type=str,
        choices=["get_started", "lab_exercise"],
        default=None,
        help=(
            "Override page type detection.\n"
            "If not set, detected automatically from PAGE_TYPE: in prompts.txt"
        )
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip the git staging step"
    )
    return parser.parse_args()


def _resolve_template(page_type: str, override: str) -> str:
    """
    Auto-select the right template for the page type if not explicitly provided.
      get_started  → getstarted.md
      lab_exercise → azureaiTemplate.md
    """
    if override:
        return override
    return "getstarted.md" if page_type == "get_started" else "azureaiTemplate.md"


def run(template_name=None, output_filename=None, page_type_override=None, skip_commit=False):
    print("\n" + "═" * 58)
    print("  🚀 CloudLabs AI Lab Guide Generator")
    print("═" * 58 + "\n")

    # ── Step 1: Load all inputs ────────────────────────────────────────────────
    print("── Step 1: Loading inputs ──────────────────────────────────")
    prompt_text = loader.load_prompt()
    yaml_rules = loader.load_yaml_rules()
    screenshot_files = loader.load_screenshots()

    # ── Step 2: Detect page type ───────────────────────────────────────────────
    print("\n── Step 2: Detecting page type ─────────────────────────────")
    if page_type_override:
        page_type = page_type_override
        print(f"[App] ✅ Page type overridden via --page-type: {page_type}")
    else:
        page_type = prompt_builder.detect_page_type(prompt_text)

    # Auto-select template based on page type
    resolved_template = _resolve_template(page_type, template_name)
    template_content, template_name_used = loader.load_template(resolved_template)

    print(f"[App]    Page type  : {page_type}")
    print(f"[App]    Template   : {template_name_used}")

    # ── Step 3: Screenshot analysis (Phase 2 stub) ─────────────────────────────
    print("\n── Step 3: Screenshot Analysis ─────────────────────────────")
    screenshot_context = image_analyzer.analyze_screenshots(screenshot_files)

    # ── Step 4: Fetch MS Learn documentation ──────────────────────────────────
    print("\n── Step 4: Fetching MS Learn docs ──────────────────────────")
    ms_learn_context = ms_learn.fetch_docs_context(prompt_text)

    # ── Step 5: Build prompts ──────────────────────────────────────────────────
    print("── Step 5: Building prompts ────────────────────────────────")
    system_prompt = prompt_builder.build_system_prompt(yaml_rules, page_type)
    user_prompt = prompt_builder.build_user_prompt(
        user_prompt=prompt_text,
        template_content=template_content,
        template_name=template_name_used,
        page_type=page_type,
        screenshot_context=screenshot_context,
        ms_learn_context=ms_learn_context
    )
    print(f"[Prompt Builder] ✅ System prompt : {len(system_prompt)} chars")
    print(f"[Prompt Builder] ✅ User prompt   : {len(user_prompt)} chars")

    # ── Step 6: Call Azure OpenAI ──────────────────────────────────────────────
    print("\n── Step 6: Calling Azure OpenAI (o4-mini) ──────────────────")
    markdown_output = ai_client.generate_lab_guide(system_prompt, user_prompt)

    # ── Step 7: Validate output ────────────────────────────────────────────────
    print("── Step 7: Validating output ───────────────────────────────")
    validator.validate(markdown_output, yaml_rules, page_type)

    # ── Step 8: Save to Labs-output/ ──────────────────────────────────────────
    print("── Step 8: Saving output ───────────────────────────────────")
    saved_path = output_writer.save(
        markdown_content=markdown_output,
        prompt_text=prompt_text,
        filename=output_filename
    )

    # ── Step 9: Git staging ────────────────────────────────────────────────────
    if not skip_commit:
        print("── Step 9: Git staging ─────────────────────────────────────")
        gitCommit.stage_file(saved_path)
    else:
        print("── Step 9: Git staging skipped (--no-commit flag) ──────────")

    # ── Done ───────────────────────────────────────────────────────────────────
    print("\n" + "═" * 58)
    print("  ✅ Lab guide generation complete!")
    print(f"  📄 Page type : {page_type}")
    print(f"  📄 File      : Labs-output/{os.path.basename(saved_path)}")
    print("═" * 58 + "\n")

    return saved_path


if __name__ == "__main__":
    args = parse_args()
    try:
        run(
            template_name=args.template,
            output_filename=args.output,
            page_type_override=args.page_type,
            skip_commit=args.no_commit
        )
    except (FileNotFoundError, ValueError, EnvironmentError) as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user.\n")
        sys.exit(0)