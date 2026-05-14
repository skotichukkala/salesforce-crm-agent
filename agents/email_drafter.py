import anthropic
import json
import time
from trust_layer.pii_guard import log_audit
from observability.metrics import log_metric

def draft_email(lead: dict, qualification: dict, routing: dict, api_key: str) -> dict:
    """Draft a personalized follow-up email for a lead."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are an expert Salesforce sales email writer.

Draft a personalized follow-up email for this lead.

Lead info:
- Name: {lead['name']}
- Title: {lead['title']}
- Company: {lead['company']}
- Industry: {lead['industry']}
- Notes: {lead['notes']}
- Lead score: {qualification['score']}
- Recommended action: {qualification['next_action']}
- Assigned rep: {routing['assigned_rep']}

Rules:
- Subject line must be specific and compelling (no generic "Following up")
- 3-4 short paragraphs max
- Reference their specific industry/role
- Clear single CTA at the end
- Professional but warm tone
- Sign off as the assigned rep

Return JSON with:
- subject: email subject line
- body: full email body (use \\n for line breaks)
- cta: the specific call to action
- tone: "urgent" | "consultative" | "nurture"

Return ONLY valid JSON, no markdown, no explanation.
"""

    start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
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
        result["to"] = lead["email"]
        result["lead_name"] = lead["name"]

        log_metric(
            agent="email_drafter",
            action=f"draft_email_{lead['id']}",
            duration_seconds=duration,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            success=True
        )

        log_audit(
            action="email_draft",
            input_summary=f"Lead {lead['id']} - {lead['company']}",
            output_summary=f"Subject: {result['subject'][:80]}",
            pii_detected=False
        )

        return result

    except Exception as e:
        duration = time.time() - start
        log_metric(
            agent="email_drafter",
            action=f"draft_email_{lead['id']}",
            duration_seconds=duration,
            input_tokens=0,
            output_tokens=0,
            success=False,
            error=str(e)
        )
        raise