# Salesforce CRM Agent — MCP-Powered Multi-Agent Pipeline

An Agentforce-inspired autonomous CRM pipeline that qualifies leads, routes them to the right sales rep, and drafts personalized outreach emails — with an Einstein Trust Layer for PII protection and full audit logging.

> Built as a hands-on implementation of Salesforce's Agentforce architecture using MCP servers, multi-agent orchestration, and enterprise-grade trust/governance patterns.

---

## Demo

```
[MCP] Found 5 total leads

AGENT 1: Lead Qualifier
  🔥 Michael Chen (FinancePlus) → HOT | 95% confidence
     Ready to buy, comparing with competitor. Follow up ASAP.
  🌤 James Patel (TechCorp Inc) → WARM | 75% confidence
  🌤 David Kim (StartupXYZ) → WARM | 85% confidence
  ❄️ Emily Rodriguez (HealthNet) → COLD | 85% confidence

AGENT 2: Lead Router
  ✓ Michael Chen → Alex Turner (Finance specialist) | P1 | Within 1 hour

AGENT 3: Email Drafter
  📧 Subject: FinancePlus + Salesforce: Decision-making timeline & competitive comparison

TRUST LAYER
  Total AI calls logged: 10 | PII masking events: 5
```

---

## Architecture

```
User Query
     ↓
MCP Server — exposes CRM tools (get_leads, filter, update)
     ↓
Agent 1: Lead Qualifier  →  hot / warm / cold + confidence score
     ↓
Agent 2: Lead Router     →  matches lead to best available sales rep
     ↓
Agent 3: Email Drafter   →  personalized outreach email with CTA
     ↓
Trust Layer              →  PII masking + audit log on every AI call
```

---

## Key Features

**MCP Server**
Modular tool layer exposing CRM operations — get all leads, filter by temperature, update notes. Designed to mirror how Salesforce's Agentforce connects to external data sources.

**Lead Qualifier Agent**
Scores each lead hot/warm/cold with confidence percentage, reasoning, urgency level, and specific next action. PII (email, phone) is masked before any data reaches the LLM.

**Lead Router Agent**
Matches qualified leads to the best available sales rep based on industry expertise and lead urgency. Assigns priority (P1/P2/P3) and suggested contact window.

**Email Drafter Agent**
Generates role-specific, personalized outreach emails with a compelling subject line and single clear CTA. References the lead's industry, title, and specific situation.

**Einstein Trust Layer**
- PII masking: strips emails, phone numbers, SSNs before every LLM call
- Audit logging: every AI action logged with timestamp, action type, and output summary
- Zero raw personal data sent to external APIs

---

## Quickstart

```bash
# 1. Clone and setup
git clone https://github.com/skotichukkala/salesforce-crm-agent.git
cd salesforce-crm-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Add your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 3. Run the pipeline
python3 main.py           # process all leads
python3 main.py hot       # hot leads only
python3 main.py cold      # cold leads only
```

---

## Project Structure

```
salesforce-crm-agent/
├── main.py                  # Orchestrator — runs full pipeline
├── mcp/
│   └── crm_server.py        # MCP server exposing CRM tools
├── agents/
│   ├── qualifier.py         # Lead scoring agent
│   ├── router.py            # Sales rep routing agent
│   └── email_drafter.py     # Personalized email agent
├── trust_layer/
│   └── pii_guard.py         # PII masking + audit logging
└── data/
    └── leads.json           # Mock CRM lead dataset
```

---

## Tech Stack

- **Language:** Python 3.13
- **AI:** Anthropic Claude (claude-sonnet-4-5) via API
- **Agent Pattern:** MCP server + tool-calling + prompt-chained agents
- **Trust/Governance:** PII masking, JSONL audit trail
- **Infrastructure:** Modular microservice-style architecture

---

## Results

- 5 leads processed end-to-end in under 60 seconds
- PII masked on every LLM call — zero raw personal data sent to API
- 10 AI actions fully audited with timestamps
- Hot leads identified with 95% confidence and routed within 1 hour SLA

---

## Why This Project

Salesforce's Agentforce platform uses the same core patterns implemented here: MCP servers for tool access, multi-agent orchestration for complex workflows, and a Trust Layer for enterprise data governance. This project demonstrates those patterns independently — built from scratch to understand the architecture deeply.

---

## Author

**Srivalli Kotichukkala**  
