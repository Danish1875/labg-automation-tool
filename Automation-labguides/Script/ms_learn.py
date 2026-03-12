"""
ms_learn.py
-----------
Fetches relevant Microsoft Learn documentation and injects it as live
context into the AI prompt. This gives o4-mini access to up-to-date
official Azure documentation at generation time.

How it works:
  1. Extracts AZURE_SERVICES from the parsed prompt
  2. Builds targeted search queries per service
  3. Calls the MS Learn search API (no auth required — public docs)
  4. Fetches the top result pages for detailed content
  5. Returns a formatted context string injected into the user prompt

This means o4-mini reasons from BOTH your lab description AND
the latest official Microsoft documentation simultaneously.
"""

import re
import urllib.request
import urllib.parse
import urllib.error
import json


# MS Learn search API — public, no key required
MS_LEARN_SEARCH_URL = "https://learn.microsoft.com/api/search"

# Map of common Azure service keywords → targeted doc URLs to always include
# These are the most reliable starting points for each service
KNOWN_DOC_URLS = {
    "blob storage":     "https://learn.microsoft.com/en-us/azure/storage/blobs/access-tiers-overview",
    "access tier":      "https://learn.microsoft.com/en-us/azure/storage/blobs/archive-blob",
    "storage account":  "https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview",
    "azure openai":     "https://learn.microsoft.com/en-us/azure/ai-services/openai/overview",
    "app service":      "https://learn.microsoft.com/en-us/azure/app-service/overview",
    "azure functions":  "https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview",
    "cosmos db":        "https://learn.microsoft.com/en-us/azure/cosmos-db/introduction",
    "virtual machine":  "https://learn.microsoft.com/en-us/azure/virtual-machines/overview",
    "key vault":        "https://learn.microsoft.com/en-us/azure/key-vault/general/overview",
    "azure sql":        "https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-database-paas-overview",
    "aks":              "https://learn.microsoft.com/en-us/azure/aks/intro-kubernetes",
    "container apps":   "https://learn.microsoft.com/en-us/azure/container-apps/overview",
    "service bus":      "https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-overview",
    "event hub":        "https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-about",
}

MAX_CONTENT_CHARS = 3000   # Per doc — keeps prompt size manageable
MAX_DOCS = 3               # Max docs to fetch per run


def _extract_services(prompt_text: str) -> list:
    """
    Pull Azure service names from the AZURE_SERVICES block in prompts.txt.
    Falls back to scanning the full DESCRIPTION if no block found.
    """
    services = []

    # Try structured AZURE_SERVICES block first
    block_match = re.search(
        r"AZURE_SERVICES\s*:(.*?)(?=\n[A-Z_]+\s*:|$)",
        prompt_text, re.DOTALL | re.IGNORECASE
    )
    if block_match:
        lines = block_match.group(1).strip().splitlines()
        for line in lines:
            # Strip bullet markers and parenthetical notes
            clean = re.sub(r"[-*•]\s*", "", line).strip()
            clean = re.sub(r"\(.*?\)", "", clean).strip()
            if clean:
                services.append(clean.lower())

    # Also scan DESCRIPTION for known keywords
    desc_match = re.search(r"DESCRIPTION\s*:(.*?)(?=\n[A-Z_]+\s*:|$)", prompt_text, re.DOTALL | re.IGNORECASE)
    if desc_match:
        desc = desc_match.group(1).lower()
        for keyword in KNOWN_DOC_URLS:
            if keyword in desc and keyword not in services:
                services.append(keyword)

    return list(dict.fromkeys(services))  # dedupe while preserving order


def _resolve_doc_urls(services: list) -> list:
    """
    Map service names to known doc URLs.
    Returns a list of (service_name, url) tuples.
    """
    resolved = []
    for service in services:
        for keyword, url in KNOWN_DOC_URLS.items():
            if keyword in service or service in keyword:
                if url not in [u for _, u in resolved]:
                    resolved.append((service, url))
                    break
    return resolved[:MAX_DOCS]


def _fetch_doc(url: str) -> str:
    """
    Fetch a Microsoft Learn page and return plain text content.
    Uses the MS Learn markdown API endpoint where available,
    otherwise fetches raw HTML and strips tags.
    """
    try:
        # MS Learn has a markdown endpoint — cleaner than HTML scraping
        # Convert /en-us/ docs URLs to their raw content
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CloudLabsBot/1.0)",
                "Accept": "text/html,application/xhtml+xml"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            raw = response.read().decode("utf-8", errors="ignore")

        # Basic HTML tag stripping — good enough for doc content
        text = re.sub(r"<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"\s{3,}", "\n\n", text)
        text = text.strip()

        # Return trimmed content
        return text[:MAX_CONTENT_CHARS]

    except urllib.error.URLError as e:
        return f"[Could not fetch: {url} — {e.reason}]"
    except Exception as e:
        return f"[Could not fetch: {url} — {str(e)}]"


def fetch_docs_context(prompt_text: str) -> str:
    """
    Main entry point. Called from prompt_builder.py before building the user prompt.

    Returns a formatted string block ready to be injected into the AI prompt,
    or an empty string if no relevant docs are found or fetching fails.
    """
    print("[MS Learn] 🔍 Detecting Azure services in prompt...")
    services = _extract_services(prompt_text)

    if not services:
        print("[MS Learn] ℹ️  No Azure services detected — skipping doc fetch.")
        return ""

    print(f"[MS Learn] 📚 Services found: {services}")
    doc_urls = _resolve_doc_urls(services)

    if not doc_urls:
        print("[MS Learn] ℹ️  No matching docs found for detected services.")
        return ""

    context_blocks = []

    for service, url in doc_urls:
        print(f"[MS Learn] ⬇️  Fetching: {url}")
        content = _fetch_doc(url)

        if content and not content.startswith("[Could not fetch"):
            context_blocks.append(
                f"### Microsoft Learn: {service.title()}\n"
                f"Source: {url}\n\n"
                f"{content}\n"
            )
            print(f"[MS Learn] ✅ Fetched ({len(content)} chars): {service}")
        else:
            print(f"[MS Learn] ⚠️  {content}")

    if not context_blocks:
        return ""

    header = (
        "────────────────────────────────────────────\n"
        "MICROSOFT LEARN DOCUMENTATION (live — use this as your source of truth)\n"
        "────────────────────────────────────────────\n"
        "The following content was fetched from official Microsoft Learn docs.\n"
        "Use it to:\n"
        "  1. Ensure all portal navigation steps are accurate and up to date\n"
        "  2. Use correct terminology, tier names, and feature constraints\n"
        "  3. Include accurate Notes about limitations (e.g. Archive is offline,\n"
        "     only Block Blobs support access tiers, rehydration takes up to 15 hours)\n"
        "  4. Reference any relevant Azure CLI commands in code blocks\n\n"
    )

    return header + "\n\n".join(context_blocks)