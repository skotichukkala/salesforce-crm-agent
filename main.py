import os
import json
from dotenv import load_dotenv
from mcp.crm_server import call_tool
from agents.qualifier import qualify_all_leads
from agents.router import route_lead
from agents.email_drafter import draft_email
from trust_layer.pii_guard import get_audit_log

load_dotenv()

def print_separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def run_pipeline(mode: str = "all"):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in .env file")

    print_separator("SALESFORCE CRM AGENT — Starting Pipeline")

    # Step 1: Retrieve leads via MCP
    print("\n[MCP] Fetching leads from CRM...")
    if mode == "cold":
        leads = call_tool("get_cold_leads", days_threshold=30)
        print(f"[MCP] Found {len(leads)} cold leads (no contact in 30+ days)")
    elif mode == "hot":
        leads = call_tool("get_hot_leads")
        print(f"[MCP] Found {len(leads)} hot leads")
    else:
        leads = call_tool("get_all_leads")
        print(f"[MCP] Found {len(leads)} total leads")

    if not leads:
        print("No leads found for this filter.")
        return

    # Step 2: Qualify all leads
    print_separator("AGENT 1: Lead Qualifier")
    qualifications = qualify_all_leads(leads, api_key)

    print("\nQualification Results:")
    for q in qualifications:
        emoji = {"hot": "🔥", "warm": "🌤", "cold": "❄️"}[q["score"]]
        print(f"  {emoji} {q['lead_name']} ({q['company']}) → {q['score'].upper()} | {q['confidence']}% confidence")
        print(f"     {q['reasoning']}")
        print(f"     Next: {q['next_action']}")

    # Step 3: Route hot + warm leads
    print_separator("AGENT 2: Lead Router")
    priority_leads = [q for q in qualifications if q["score"] in ["hot", "warm"]]
    routings = []

    for qual in priority_leads:
        lead = next(l for l in leads if l["id"] == qual["lead_id"])
        routing = route_lead(lead, qual, api_key)
        routings.append(routing)
        print(f"  ✓ {routing['lead_name']} → {routing['assigned_rep']} | {routing['priority']} | {routing['suggested_contact_time']}")

    # Step 4: Draft emails for hot leads only
    print_separator("AGENT 3: Email Drafter")
    hot_leads = [q for q in qualifications if q["score"] == "hot"]
    emails = []

    for qual in hot_leads:
        lead = next(l for l in leads if l["id"] == qual["lead_id"])
        routing = next(r for r in routings if r["lead_id"] == qual["lead_id"])
        email = draft_email(lead, qual, routing, api_key)
        emails.append(email)
        print(f"\n  📧 Email for {email['lead_name']} ({email['to']})")
        print(f"  Subject: {email['subject']}")
        print(f"  ---")
        print(f"  {email['body'][:300]}...")
        print(f"  ---")
        print(f"  CTA: {email['cta']}")

    # Step 5: Show audit log
    print_separator("TRUST LAYER — Audit Log")
    logs = get_audit_log()
    print(f"  Total AI calls logged: {len(logs)}")
    pii_events = [l for l in logs if l["pii_detected"]]
    print(f"  PII masking events: {len(pii_events)}")
    print(f"\n  Recent entries:")
    for entry in logs[-5:]:
        pii_flag = "🛡 PII masked" if entry["pii_detected"] else "✓ Clean"
        print(f"  [{entry['timestamp']}] {entry['action']} | {pii_flag}")
        print(f"    → {entry['output_summary']}")

    # Save full results
    results = {
        "leads_processed": len(leads),
        "qualifications": qualifications,
        "routings": routings,
        "emails": emails,
        "audit_entries": len(logs)
    }
    with open("data/results.json", "w") as f:
        json.dump(results, f, indent=2)

    print_separator("PIPELINE COMPLETE")
    print(f"  ✅ {len(leads)} leads processed")
    print(f"  🔥 {len(hot_leads)} hot leads with drafted emails")
    print(f"  📋 {len(routings)} leads routed to reps")
    print(f"  🛡  {len(logs)} AI calls audited")
    print(f"  📁 Full results saved to data/results.json")

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    run_pipeline(mode)