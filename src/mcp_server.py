"""
mcp_server.py — the Mosaic Node's MCP endpoint (the PRIMARY access path).

Exposes ONE tool, `consult_risklore(situation)`, over MCP (stdio). Any MCP-capable agent
(Claude Desktop, Cursor, an in-house agent) points its MCP config at this file and its
existing assistant silently gains citable precedent — the analyst's workflow changes by
zero clicks.

It calls the SAME shared logic as the dashboard (query.consult_with_citations), so the
retrieval + provenance never diverge between surfaces.

Add to an MCP client config (e.g. Claude Desktop claude_desktop_config.json):

  "mcpServers": {
    "mosaic-risklore": {
      "command": "/ABSOLUTE/PATH/mosaic/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/mosaic/src/mcp_server.py"]
    }
  }

Run standalone (for a smoke test):  .venv/bin/python src/mcp_server.py
"""

import os
import sys

# Make imports + .env work no matter how the MCP client launches this file.
_HERE = os.path.dirname(os.path.abspath(__file__))          # …/src
_ROOT = os.path.dirname(_HERE)                              # repo root
sys.path.insert(0, _HERE)

from dotenv import load_dotenv
load_dotenv(os.path.join(_ROOT, ".env"))

from mcp.server.fastmcp import FastMCP
from config import PACK_DATASET, PACK_LABEL
from query import consult_with_citations

mcp = FastMCP("mosaic-risklore")


@mcp.tool()
async def consult_risklore(situation: str) -> str:
    """Consult the installed RiskLore pack for precedent on a described risk situation.

    Given a free-text description of a financial risk situation (a counterparty, a bank,
    a transaction pattern, a fraud scenario), returns the closest historical
    financial-failure precedent from the pack, the warning signs and risk factors it
    shares, an investigation playbook, and CITATIONS to the primary-source regulatory or
    judicial documents behind the precedent. Use this to ground risk assessments in
    verified precedent; a human makes the final decision.

    Args:
        situation: A plain-language description of the risk situation to assess.
    """
    result = await consult_with_citations(situation, PACK_DATASET)
    lines = [result["answer"].strip(), ""]
    citations = result.get("citations") or []
    if citations:
        lines.append("Sources (primary-source provenance):")
        for c in citations:
            year = f" ({c['year']})" if c.get("year") else ""
            for s in c.get("sources", []):
                url = f" — {s['url']}" if s.get("url") else ""
                lines.append(f"  - {c['institution']}{year}: {s['label']}{url}")
    else:
        lines.append("(No specific pack precedent matched; treat as general guidance.)")
    lines.append("")
    lines.append(f"[Answered from the installed pack {PACK_LABEL}. Decision support only — "
                 "human judgment is final.]")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()   # stdio transport — what MCP clients (Claude Desktop, Cursor) speak
