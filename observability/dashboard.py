from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from observability.metrics import get_summary, get_all_metrics
import json

app = FastAPI(title="CRM Agent Observability Dashboard")

@app.get("/", response_class=HTMLResponse)
def dashboard():
    summary = get_summary()
    metrics = get_all_metrics()

    if not summary:
        return "<h2>No metrics yet. Run python3 main.py first.</h2>"

    by_agent = summary.get("by_agent", {})

    agent_rows = ""
    for agent, data in by_agent.items():
        agent_rows += f"""
        <tr>
            <td>{agent}</td>
            <td>{data['calls']}</td>
            <td>{data['avg_latency']}s</td>
            <td>{data['total_tokens']:,}</td>
            <td>${data['total_cost']:.6f}</td>
            <td>{data['avg_confidence'] or 'N/A'}</td>
        </tr>"""

    recent_rows = ""
    for m in reversed(metrics[-10:]):
        status = "✅" if m["success"] else "❌"
        conf = f"{m['confidence']}%" if m["confidence"] else "—"
        recent_rows += f"""
        <tr>
            <td>{m['timestamp'][11:19]}</td>
            <td>{m['agent']}</td>
            <td>{m['duration_seconds']}s</td>
            <td>{m['total_tokens']}</td>
            <td>${m['estimated_cost_usd']:.6f}</td>
            <td>{conf}</td>
            <td>{status}</td>
        </tr>"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CRM Agent Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; color: #f8fafc; }}
        .subtitle {{ color: #64748b; font-size: 0.875rem; margin-bottom: 2rem; }}
        .cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 1.25rem; border: 1px solid #334155; }}
        .card-label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
        .card-value {{ font-size: 1.75rem; font-weight: 600; color: #f8fafc; }}
        .card-value.green {{ color: #4ade80; }}
        .card-value.blue {{ color: #60a5fa; }}
        .card-value.yellow {{ color: #fbbf24; }}
        .card-value.purple {{ color: #a78bfa; }}
        h2 {{ font-size: 1rem; margin-bottom: 1rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; margin-bottom: 2rem; }}
        th {{ background: #0f172a; padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; color: #64748b; text-transform: uppercase; }}
        td {{ padding: 0.75rem 1rem; border-top: 1px solid #334155; font-size: 0.875rem; }}
        tr:hover td {{ background: #263548; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; }}
        .badge-blue {{ background: #1d4ed8; color: #bfdbfe; }}
        .refresh {{ color: #475569; font-size: 0.75rem; margin-bottom: 1rem; }}
    </style>
</head>
<body>
    <h1>🤖 CRM Agent Observability Dashboard</h1>
    <p class="subtitle">MCP-Powered Multi-Agent Pipeline — Auto-refreshes every 10 seconds</p>
    <p class="refresh">Last updated: {metrics[-1]['timestamp'][11:19] if metrics else 'N/A'} UTC</p>

    <div class="cards">
        <div class="card">
            <div class="card-label">Total AI Calls</div>
            <div class="card-value blue">{summary['total_runs']}</div>
        </div>
        <div class="card">
            <div class="card-label">Total Cost</div>
            <div class="card-value green">${summary['total_cost_usd']:.4f}</div>
        </div>
        <div class="card">
            <div class="card-label">Avg Latency</div>
            <div class="card-value yellow">{summary['avg_latency_seconds']}s</div>
        </div>
        <div class="card">
            <div class="card-label">Success Rate</div>
            <div class="card-value green">{summary['success_rate_pct']}%</div>
        </div>
        <div class="card">
            <div class="card-label">Total Tokens</div>
            <div class="card-value purple">{summary['total_tokens']:,}</div>
        </div>
    </div>

    <h2>By Agent</h2>
    <table>
        <thead>
            <tr>
                <th>Agent</th>
                <th>Calls</th>
                <th>Avg Latency</th>
                <th>Total Tokens</th>
                <th>Total Cost</th>
                <th>Avg Confidence</th>
            </tr>
        </thead>
        <tbody>{agent_rows}</tbody>
    </table>

    <h2>Recent Calls</h2>
    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Agent</th>
                <th>Duration</th>
                <th>Tokens</th>
                <th>Cost</th>
                <th>Confidence</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>{recent_rows}</tbody>
    </table>
</body>
</html>"""
    return html

@app.get("/api/summary")
def api_summary():
    return get_summary()

@app.get("/api/metrics")
def api_metrics():
    return get_all_metrics()