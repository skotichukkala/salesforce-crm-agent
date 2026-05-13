import re
import json
import os
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "data" / "audit_log.jsonl"

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+?1?\s?)?(\(?\d{3}\)?[\s\-.]?)(\d{3}[\s\-.]?\d{4})\b",
    "ssn":   r"\b\d{3}-\d{2}-\d{4}\b",
}

def mask_pii(text: str) -> tuple[str, dict]:
    """Mask PII in text. Returns masked text and a map of replacements."""
    masked = text
    found = {}
    for label, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, masked)
        for i, match in enumerate(matches):
            original = match if isinstance(match, str) else "".join(match)
            placeholder = f"[{label.upper()}_{i+1}]"
            masked = masked.replace(original, placeholder, 1)
            found[placeholder] = original
    return masked, found

def restore_pii(text: str, pii_map: dict) -> str:
    """Restore masked PII back into text."""
    for placeholder, original in pii_map.items():
        text = text.replace(placeholder, original)
    return text

def log_audit(action: str, input_summary: str, output_summary: str, pii_detected: bool):
    """Append an audit entry to the log file."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "input_summary": input_summary[:200],
        "output_summary": output_summary[:200],
        "pii_detected": pii_detected,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_audit_log() -> list[dict]:
    """Read all audit log entries."""
    if not LOG_PATH.exists():
        return []
    entries = []
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries