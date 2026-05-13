import json
import os
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "leads.json"

def load_leads():
    with open(DATA_PATH) as f:
        return json.load(f)

def get_all_leads() -> list[dict]:
    """Retrieve all leads from the CRM."""
    return load_leads()

def get_lead_by_id(lead_id: str) -> dict | None:
    """Retrieve a specific lead by ID."""
    leads = load_leads()
    return next((l for l in leads if l["id"] == lead_id), None)

def get_cold_leads(days_threshold: int = 30) -> list[dict]:
    """Get leads with no contact in N days."""
    leads = load_leads()
    return [l for l in leads if l["last_contact_days_ago"] >= days_threshold]

def get_hot_leads() -> list[dict]:
    """Get leads that are demo-requested and budget confirmed."""
    leads = load_leads()
    return [l for l in leads if l["demo_requested"] and l["budget_confirmed"]]

def update_lead_notes(lead_id: str, notes: str) -> bool:
    """Update notes for a lead."""
    leads = load_leads()
    for lead in leads:
        if lead["id"] == lead_id:
            lead["notes"] = notes
            with open(DATA_PATH, "w") as f:
                json.dump(leads, f, indent=2)
            return True
    return False

TOOLS = {
    "get_all_leads": get_all_leads,
    "get_lead_by_id": get_lead_by_id,
    "get_cold_leads": get_cold_leads,
    "get_hot_leads": get_hot_leads,
    "update_lead_notes": update_lead_notes,
}

def call_tool(tool_name: str, **kwargs):
    """Execute a CRM tool by name."""
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOLS[tool_name](**kwargs)