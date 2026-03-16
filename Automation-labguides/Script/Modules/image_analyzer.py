"""
image_analyzer.py
-----------------
Phase 2 — Screenshot Analysis (ACTIVE)

Reads screenshots from Screenshot/<lab_folder>/ (e.g. Screenshot/storageacc/),
sends each image to Azure OpenAI GPT-4o vision model, and returns ordered step
descriptions that are injected into the AI prompt as context.

The AI then uses these descriptions to:
  1. Sequence steps in the exact order screenshots were taken
  2. Embed screenshot references inline: ![](../media/filename.png)
  3. Match UI element names exactly as seen in the screenshots

Naming convention for screenshots:
  01_open_storage_account.png
  02_click_containers.png
  03_create_container.png
  ...
  Numeric prefix drives ordering. Snagit annotations show click numbers.
"""

import os
import base64
import re


def get_repo_root() -> str:
    modules_dir = os.path.dirname(os.path.abspath(__file__))  # .../Script/Modules/
    script_dir  = os.path.dirname(modules_dir)                # .../Script/
    return os.path.dirname(script_dir)                        # .../Automation-labguides/


def _encode_image(image_path: str) -> str:
    """Base64-encode a local image file for the OpenAI vision API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_media_type(filename: str) -> str:
    """Return the correct MIME type based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def _load_vision_client():
    """
    Load the Azure OpenAI client for GPT-4o vision calls.
    Uses the same .env as ai_client.py — reads from Script/.env.
    """
    from dotenv import load_dotenv
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    env_path  = os.path.join(os.path.dirname(_this_dir), ".env")
    load_dotenv(dotenv_path=env_path)

    from openai import AzureOpenAI

    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key    = os.getenv("AZURE_OPENAI_KEY")
    # Vision deployment — use gpt-4o if you have it, falls back to same deployment
    deployment = os.getenv("AZURE_OPENAI_VISION_DEPLOYMENT", os.getenv("AZURE_OPENAI_DEPLOYMENT"))

    if not endpoint or not api_key:
        raise EnvironmentError(
            "[Image Analyzer] ❌ Missing Azure OpenAI credentials in .env.\n"
            "  Add AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4o (or your vision-capable deployment name)."
        )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-12-01-preview"
    )
    return client, deployment


def _describe_screenshot(client, deployment: str, image_path: str, step_number: int) -> str:
    """
    Send a single screenshot to GPT-4o vision and return a structured step description.
    """
    filename = os.path.basename(image_path)
    b64      = _encode_image(image_path)
    media    = _get_media_type(filename)

    response = client.chat.completions.create(
        model=deployment,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"This is screenshot number {step_number} from an Azure Portal lab exercise.\n\n"
                        "The screenshot may contain numbered annotations (1, 2, 3...) indicating "
                        "the sequence of clicks or actions the user must perform.\n\n"
                        "Please describe:\n"
                        "1. Which Azure Portal page or blade is shown\n"
                        "2. Each numbered action in order — the exact UI element name, "
                        "   where it is on the screen, and what the user does (click, type, select, etc.)\n"
                        "3. Any important field values, dropdown selections, or settings visible\n"
                        "4. What the expected result or next screen would be after completing these actions\n\n"
                        "Be precise with UI element names exactly as they appear in the portal. "
                        "Format your response as a numbered list of actions."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url":    f"data:{media};base64,{b64}",
                        "detail": "high"
                    }
                }
            ]
        }],
        max_tokens=1000
    )

    return response.choices[0].message.content.strip()


def scan_screenshot_folder(lab_folder: str) -> list:
    """
    Scan Screenshot/<lab_folder>/ for image files.
    Returns sorted list of absolute file paths (sorted by numeric prefix).

    Args:
        lab_folder: subfolder name inside Screenshot/ e.g. 'storageacc'
    """
    root           = get_repo_root()
    screenshot_dir = os.path.join(root, "Screenshot", lab_folder)

    if not os.path.exists(screenshot_dir):
        print(f"[Image Analyzer] ⚠️  Folder not found: Screenshot/{lab_folder}/")
        print(f"[Image Analyzer]    Create it and add your .png screenshots.")
        return []

    valid_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    files = [
        f for f in os.listdir(screenshot_dir)
        if os.path.splitext(f)[1].lower() in valid_exts
    ]

    if not files:
        print(f"[Image Analyzer] ℹ️  No images found in Screenshot/{lab_folder}/")
        return []

    # Sort by leading number in filename, then alphabetically
    def sort_key(filename):
        match = re.match(r"(\d+)", filename)
        return (int(match.group(1)) if match else 9999, filename)

    files.sort(key=sort_key)
    return [os.path.join(screenshot_dir, f) for f in files]


def analyze_screenshots(screenshot_files: list) -> list:
    """
    Main entry point called from app.py.

    If screenshot_files is empty → returns [] silently (no-op).
    If files exist → loads vision client, describes each image,
    returns list of dicts for prompt_builder.py to consume.

    Args:
        screenshot_files: List of absolute image paths from scan_screenshot_folder()
                          or from loader.py passing the lab folder name.

    Returns:
        List of dicts:
        [
          {
            "step_number": 1,
            "filename":    "01_open_storage.png",
            "path":        "/abs/path/to/screenshot",
            "description": "1. Click on 'Storage accounts' in the left nav..."
          },
          ...
        ]
    """
    if not screenshot_files:
        print("[Image Analyzer] 📸 No screenshots provided — skipping image analysis.")
        return []

    print(f"[Image Analyzer] 📸 {len(screenshot_files)} screenshot(s) found — analysing with GPT-4o vision...")

    try:
        client, deployment = _load_vision_client()
        print(f"[Image Analyzer] 🔗 Vision model: {deployment}\n")
    except EnvironmentError as e:
        print(f"{e}")
        print("[Image Analyzer] ⚠️  Skipping image analysis — continuing without screenshot context.")
        return []

    results = []

    for i, filepath in enumerate(screenshot_files, start=1):
        filename = os.path.basename(filepath)
        print(f"[Image Analyzer] 🖼️  Analysing ({i}/{len(screenshot_files)}): {filename}")

        try:
            description = _describe_screenshot(client, deployment, filepath, i)
            results.append({
                "step_number": i,
                "filename":    filename,
                "path":        filepath,
                "description": description
            })
            print(f"[Image Analyzer] ✅ Done: {filename}\n")

        except Exception as e:
            print(f"[Image Analyzer] ⚠️  Failed to analyse {filename}: {e}")
            print(f"[Image Analyzer]    Skipping this screenshot and continuing.\n")
            continue

    print(f"[Image Analyzer] ✅ Analysis complete — {len(results)}/{len(screenshot_files)} screenshots described.\n")
    return results