import anthropic
import json
import time
from trust_layer.pii_guard import mask_pii, log_audit
from observability.metrics import log_metric

def qualify_lead(lead: dict, api_key: str) -> dict:
    """Score a lead as hot/warm/cold with reasoning."""
    client = anthropic.Anthropic(api_key=api_key)

    lead_text = json.dumps(lead, indent=2)
    masked_text, pii_map = mask_pii(lead_text)

    prompt = f"""You are a Salesforce CRM lead qualification expert.

Analyze this lead and return a JSON object with:
- score: "hot" | "warm" | "cold"
- confidence: 0-100
- reasoning: 2-3 sentence explanation
- next_action: specific recommended next step
- urgency: "immediate" | "this_week" | "this_month" | "low"

Lead data:
{masked_text}

Scoring guide:
- HOT: demo requested + budget confirmed + recent contact + high engagement
- WARM: some interest signals but missing key qualifiers
- COLD: low engagement, no recent contact, no demo/budget

Return ONLY valid JSON, no markdown, no explanation.
"""

    start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
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
        result["company"] = lead["company"]

        log_metric(
            agent="qualifier",
            action=f"qualify_lead_{lead['id']}",
            duration_seconds=duration,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            confidence=result.get("confidence"),
            success=True
        )

        log_audit(
            action="lead_qualification",
            input_summary=f"Lead {lead['id']} - {lead['company']}",
            output_summary=f"Score: {result['score']} | Confidence: {result['confidence']}",
            pii_detected=bool(pii_map)
        )

        return result

    except Exception as e:
        duration = time.time() - start
        log_metric(
            agent="qualifier",
            action=f"qualify_lead_{lead['id']}",
            duration_seconds=duration,
            input_tokens=0,
            output_tokens=0,
            success=False,
            error=str(e)
        )
        raise

def qualify_all_leads(leads: list[dict], api_key: str) -> list[dict]:
    """Qualify a list of leads."""
    results = []
    for lead in leads:
        print(f"  Qualifying {lead['name']} at {lead['company']}...")
        result = qualify_lead(lead, api_key)
        results.append(result)
    return sorted(results, key=lambda x: {"hot": 0, "warm": 1, "cold": 2}[x["score"]])