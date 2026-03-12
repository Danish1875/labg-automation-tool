"""
image_analyzer.py
-----------------
PHASE 2 — Screenshot Analysis (NOT YET ACTIVE)

This module will handle reading screenshots from Screenshot/,
interpreting the numbered visual indicators (click order),
and generating structured step descriptions to feed into the AI prompt.

────────────────────────────────────────────
HOW IT WILL WORK (Phase 2 design):
────────────────────────────────────────────
1. loader.py scans Screenshot/ and passes a sorted list of .png filenames here
2. Each screenshot is sent to Azure OpenAI GPT-4o (vision model) with a prompt like:
     "This is a numbered screenshot from a cloud lab exercise.
      Describe what the user is clicking, what UI elements are visible,
      and what step this represents. Be precise about button names and locations."
3. The response is parsed into a structured dict:
     {
       "step_number": 1,
       "filename": "step1.png",
       "description": "Click on '+ Create' button in the top left of the Azure portal..."
     }
4. These dicts are passed to prompt_builder.py as screenshot_context
5. The AI then uses them to generate accurate, screenshot-aligned steps
   and embeds: ![](../media/step1.png) inline at the correct position

────────────────────────────────────────────
NAMING CONVENTION FOR SCREENSHOTS (future):
────────────────────────────────────────────
Screenshots should be named with a numeric prefix to preserve order:
  01_open_storage_account.png
  02_click_access_tier.png
  03_select_archive.png

The Snagit tool is used to annotate screenshots with numbered click indicators.

────────────────────────────────────────────
AZURE SERVICES THAT WILL BE USED:
────────────────────────────────────────────
- Azure OpenAI GPT-4o (vision) via the same AzureOpenAI client in ai_client.py
- Images will be base64 encoded and passed in the messages[] array as image_url blocks

Example API call structure (Phase 2):
  messages = [
    {
      "role": "user",
      "content": [
        {"type": "text",      "text": "Describe this lab step screenshot..."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
      ]
    }
  ]
"""


def analyze_screenshots(screenshot_files: list) -> list:
    """
    STUB — Returns empty list until Phase 2 is implemented.

    Args:
        screenshot_files: List of .png filenames from Screenshot/ directory

    Returns:
        List of dicts: [{ step_number, filename, description }, ...]
        Currently always returns [] so the pipeline skips image context.
    """
    if screenshot_files:
        print("[Image Analyzer] 📸 Screenshot analysis is planned for Phases ahead.")
        print(f"[Image Analyzer]    {len(screenshot_files)} file(s) detected but not yet processed:")
        for f in screenshot_files:
            print(f"[Image Analyzer]    → {f}")
        print("[Image Analyzer]    Continuing without image context.\n")

    return []


# ─── Phase 2 implementation will go below this line ───────────────────────────

# def _encode_image_base64(image_path: str) -> str:
#     """Encode a local image file as a base64 string for the OpenAI vision API."""
#     import base64
#     with open(image_path, "rb") as img_file:
#         return base64.b64encode(img_file.read()).decode("utf-8")


# def _call_vision_model(client, deployment: str, image_path: str) -> str:
#     """Send a single screenshot to GPT-4o and return its step description."""
#     b64 = _encode_image_base64(image_path)
#     response = client.chat.completions.create(
#         model=deployment,
#         messages=[{
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": (
#                         "This is a numbered screenshot from a cloud lab exercise on the Azure portal. "
#                         "The numbers in the screenshot indicate the order of clicks or actions. "
#                         "Describe each numbered action precisely: what the user clicks, the exact "
#                         "UI element name, and what happens next. Format as a numbered list."
#                     )
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/png;base64,{b64}"}
#                 }
#             ]
#         }],
#         max_tokens=1000
#     )
#     return response.choices[0].message.content