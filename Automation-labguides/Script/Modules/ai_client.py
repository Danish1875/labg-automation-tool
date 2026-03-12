"""
ai_client.py
------------
Handles the Azure OpenAI API call using the o4-mini model.

Uses the openai Python SDK configured for Azure.
Credentials are loaded from Script/.env via python-dotenv.

Model: o4-mini
  - o4-mini uses max_completion_tokens (not max_tokens)
  - Does not support 'temperature' parameter (reasoning models are deterministic)
  - Returns a single completion via response.choices[0].message.content
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv


def load_client() -> tuple:
    """
    Load Azure OpenAI credentials from .env and return
    (AzureOpenAI client, deployment_name).
    """
    # Load .env from the same Script/ directory as this file
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    env_path  = os.path.join(os.path.dirname(_this_dir), ".env")
    load_dotenv(dotenv_path=env_path)

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "o4-mini")

    if not endpoint or not api_key:
        raise EnvironmentError(
            "[AI Client] ❌ Missing Azure OpenAI credentials.\n"
            "Please fill in Script/.env with:\n"
            "  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/\n"
            "  AZURE_OPENAI_KEY=your-key\n"
            "  AZURE_OPENAI_DEPLOYMENT=o4-mini"
        )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-12-01-preview"   # As per azure sdk
    )

    print(f"[AI Client] ✅ Connected to Azure OpenAI — deployment: {deployment}")
    return client, deployment


def generate_lab_guide(system_prompt: str, user_prompt: str) -> str:
    """
    Send the system + user prompt to Azure OpenAI o4-mini
    and return the raw markdown string response.

    o4-mini specifics:
      - Uses max_completion_tokens instead of max_tokens
      - No temperature support (omitted intentionally)
      - reasoning_effort="medium" balances quality vs. speed/cost
    """
    client, deployment = load_client()

    print("[AI Client] 🚀 Sending request to Azure OpenAI o4-mini...")
    print("[AI Client]    This may take 20–60 seconds for a full lab guide.\n")

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_completion_tokens=8000,    # Enough for a full multi-task lab guide
        reasoning_effort="medium"      # Options: "low" | "medium" | "high"
                                       # Use "high" for complex multi-task labs
    )

    result = response.choices[0].message.content

    if not result or not result.strip():
        raise ValueError("[AI Client] ❌ Azure OpenAI returned an empty response. Check your prompt or quota.")

    print(f"[AI Client] ✅ Response received ({len(result)} chars)")
    return result.strip()