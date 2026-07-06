"""
mcp_server.py — the Mosaic Node's MCP endpoint.

Exposes ONE tool, `consult_pack`, over MCP (stdio). Mosaic is a proof-of-concept whose
flow is explicit and USER-INITIATED: the user installs the pack via a terminal command,
their agent connects to this server over MCP, and the user then deliberately consults it.
The tool description is intentionally plain and factual — it states what the tool does and
returns, and does NOT instruct the host agent to auto-invoke it on every risk-shaped
message.

It calls the SAME shared logic as the dashboard (query.consult_with_citations), so the
retrieval + provenance never diverge between surfaces.

Add to an MCP client config (e.g. Claude Desktop claude_desktop_config.json):

  "mcpServers": {
    "mosaic-tessera": {
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
from config import PACK_DATASET, PACK_LABEL, PACK_NAME, PACK_DISPLAY
from query import consult_with_citations

mcp = FastMCP(f"mosaic-{PACK_NAME}")


def _format(result: dict) -> str:
    """Render the structured consult result as text, precedent-first, no disclaimer."""
    lines = [result["answer"].strip()]

    citations = result.get("citations") or []
    if citations:
        lines += ["", "Sources (primary-source provenance):"]
        for c in citations:
            year = f" ({c['year']})" if c.get("year") else ""
            for s in c.get("sources", []):
                url = f" — {s['url']}" if s.get("url") else ""
                lines.append(f"  - {c['institution']}{year}: {s['label']}{url}")

    lines += ["", f"[From the installed pack {PACK_LABEL}.]"]
    return "\n".join(lines)


@mcp.tool()
async def consult_pack(situation: str, map_to_situation: bool = False) -> str:
    """Look up the closest analysed precedent in the installed pack for a described financial situation.

    Returns the closest historical case from the pack, the warning signs it shares, and
    citations to the primary-source documents behind it. When map_to_situation is False,
    it also returns an invitation to map the precedent onto the situation. When
    map_to_situation is True, it additionally returns the precedent's investigation steps
    rewritten to reference the described situation's entities, instruments, and amounts.

    Args:
        situation: A plain-language description of the financial situation to find a
            precedent for.
        map_to_situation: If False (default), returns the precedent, its shared warning
            signs, and an invitation. If True, also returns the recommended playbook — in
            that case pass the FULL situation here (the original description plus anything
            the user added when confirming), so the mapping reflects everything known.
    """
    result = await consult_with_citations(situation, PACK_DATASET,
                                          map_to_situation=map_to_situation)
    return _format(result)


if __name__ == "__main__":
    mcp.run()   # stdio transport — what MCP clients (Claude Desktop, Cursor) speak
