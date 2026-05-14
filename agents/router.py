import anthropic
import json
import time
from trust_layer.pii_guard import log_audit
from observability.metrics import log_metric

SALES_REPS = [
    {"name": "Alex Turner",   "specialty": "Enterprise SaaS, Finance",     "capacity": "available"},
    {"name": "Priya Sharma",  "specialty": "Healthcare, Mid-market",        "capacity": "available"},
    {"name": "Jordan Lee",    "specialty": "Startups, SMB, Early-stage",    "capacity": "available"},
    {"name": "Marcus Webb",   "specialty": "Retail, Operations buyers",     "capacity": "busy"},
]

def route_lead(lead: dict, qualification: dict, api_key: str) -> dict:
    """Route a qualified lead to the best sales rep."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a Salesforce sales routing expert.

Available sales reps:
{json.dumps(SALES_REPS, indent=2)}

Lead summary:
- Company: {lead['company']}
- Industry: {lead['industry']}
- Title: {lead['title']}
- Revenue: ${lead['annual_revenue']:,}
- Score: {qualification['score']}
- Urgency: {qualification['urgency']}

Pick the BEST available rep and return JSON:
- assigned_rep: rep name
- reason: one sentence why this rep fits
- priority: "P1" | "P2" | "P3"
- suggested_contact_time: e.g. "Within 2 hours" or "Tomorrow morning"

Return ONLY valid JSON, no markdown, no explanation.
"""

    start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        duration = time.time() - start

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        result["lead_id"] = lead["id"]
        result["lead_name"] = lead["name"]

        log_metric(
            agent="router",
            action=f"route_lead_{lead['id']}",
            duration_seconds=duration,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            success=True
        )

        log_audit(
            action="lead_routing",
            input_summary=f"Lead {lead['id']} score={qualification['score']}",
            output_summary=f"Assigned to {result['assigned_rep']} | {result['priority']}",
            pii_detected=False
        )

        return result

    except Exception as e:
        duration = time.time() - start
        log_metric(
            agent="router",
            action=f"route_lead_{lead['id']}",
            duration_seconds=duration,
            input_tokens=0,
            output_tokens=0,
            success=False,
            error=str(e)
        )
        raise