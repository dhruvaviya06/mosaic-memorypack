# Mosaic — Tessera

> **Mosaic — senior-analyst expertise, installable.**
> **Tessera: 40 analysed cases; describe your situation, get the precedent and the playbook.**

**Mosaic** installs portable **memory packs** into a self-hosted **Node** (a Cognee
instance). **Tessera** is its flagship pack: a **casebook of senior-analyst experience** —
40 financially analysed cases, historical failures *and* investigation typologies, each
capturing how expert analysts recognised the pattern and what steps resolved (or should
have resolved) it.

Financial expertise only comes from experience. Cognee maps these cases into a knowledge
graph, matches a described situation to the precedent it most resembles, and surfaces **how
experienced analysts investigated it** — so an org's existing agent gains citable precedent
with a full evidence trail to primary sources, and **zero workflow change**.

> *Tessera shares experience, not instructions — you connect the precedent to your own case.*

---

## The contrast that makes this more than a chatbot

- **A bare LLM prescribes** — ask it about a shady counterparty and it confidently tells you
  what to do, ungrounded, putting words in an analyst's mouth.
- **Tessera recounts precedent** — it names the closest analysed case, the warning signs it
  shares, and *how the analysts in that case investigated it*, mapped onto your situation.
  Same expertise; the judgement stays human.

The aim is simple: **don't repeat mistakes financial analysts have already made.**

## The consult flow — precedent first, then map

1. **Recognise & reference** — the closest **precedent** (one line on why it matches), the
   **shared warning signs** as chips, and an **invitation** to map it onto your situation.
2. **Map (on request)** — the **recommended playbook**: the precedent's investigation steps
   rewritten to reference *your* entities, instruments, and amounts — voiced as *what
   analysts in matching cases did* (past tense, no second-person imperatives).
3. **Citations throughout** — every named precedent resolves to its primary-source document.

**Step 1 is keyless** — the precedent, chips, and citations are retrieved locally from the
pack with fastembed (no LLM key, no Cognee install). Only Step 2's tailored rewrite calls a
model. There is no per-answer disclaimer; the single framing note is shown once, at install.

## Cognee's four verbs, driving the lifecycle

| Action | Cognee lifecycle |
|--------|------------------|
| publish a pack | `remember` + `improve` |
| consult | `recall` (via `consult_pack`) |
| learn (a resolved case) | `remember` a **distilled** case into the Node's own memory |
| forget / uninstall | `forget` |

**Learn-and-forget:** when a consult is resolved, the case is **distilled** (de-identified —
names, institutions, amounts and dates stripped; only the pattern, risk factors, and matched
precedent survive) and remembered into a **separate `*_org_cases` dataset**, so the Node's
memory grows with its own cases while the curated 40 stay untouched. The raw input is never
written to a persistent dataset — it is forgotten by construction the moment the request
returns.

## Access — two surfaces, one brain

- **MCP endpoint (primary path).** One tool, `consult_pack(situation, map_to_situation)`,
  that an org's *existing* agent calls. We ship no chat UI, no agent, no LLM.
  → `src/mcp_server.py`
- **Mosaic Console (admin/demo).** A localhost dashboard to verify and demo an installed
  pack — "pgAdmin, not the bank's mobile app". → `src/consult_server.py`

Both call the same retrieval + provenance logic (`query.consult_with_citations`), so answers
never diverge between surfaces.

## The install note (the only disclaimer)

Shown once at `mesh install` and on the Console:

> *Tessera is a casebook of senior-analyst experience — 40 analysed cases. It surfaces the
> precedent your situation most resembles and how experienced analysts investigated it, so
> you don't repeat mistakes already made. Tessera shares experience, not instructions — you
> connect the precedent to your own case.*

---

## What's in the pack

- **40 curated cases** — 6 primary-source **deep** cases (Archegos, SVB, PNB/Nirav Modi, Yes
  Bank, IL&FS, DHFL), 4 **light historical** cases (LTCM, Barings, Lehman, Wirecard), and 30
  fraud / AML **typologies**. Each is seven fields of distilled expertise
  (`risk_signals`, `analyst_reasoning`, `investigation_steps`, `decision`, `outcome`,
  `lessons_learned`) plus provenance meta.
- **Round-trip proven** — `recall → export → forget → import → recall`: knowledge crosses a
  fresh Cognee instance with **zero embeddings shipped** and a verified sha256 seal.
- **Provenance** — deep and name-brand cases resolve to real regulatory/judicial (or, for
  Wirecard, press-tier) primary sources.

## Pack format (`tessera-{version}.mempack`)

A gzipped tarball, **no embeddings**:
- `graph.json` — node/edge lists (`id, type, name, text, source_ref`)
- `ontology.owl` — the ontology (7 classes / 6 relations), stored under a generic name so
  the pack format stays name-agnostic
- `provenance.json` — case → institution / year / source documents
- `cases.json` — the curated case-level text, so a fresh Node can retrieve **keyless**
  (embed locally with fastembed, no LLM) straight from the pack
- `pack.json` — manifest: platform, name, version, publisher, license, verification tier,
  node/edge counts, and a **sha256 content hash** (a *tamper* seal over graph + ontology +
  provenance — it proves the pack wasn't modified, not who published it)

## Stack

- **Cognee 1.2.2** (self-hosted: local LanceDB vector + Kuzu graph + SQLite)
- **Groq** `llama-3.3-70b-versatile` for reasoning (via cognee's `custom` provider)
- **Local `fastembed`** embeddings (`BAAI/bge-small-en-v1.5`) — no API, no quota; this *is*
  the "re-embeds locally, model-agnostic" claim
- Python 3.14, isolated in `.venv/`

## Setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env      # an LLM key is only needed to BUILD a pack or to produce the
                          # tailored playbook (Step 2). Precedent lookup (Step 1) is keyless.
```

## Run

```bash
# --- no LLM key needed (keyless — safe to run anytime) ---
.venv/bin/python src/validate_cases.py       # check case files against the schema
.venv/bin/python src/mesh.py info            # show the built pack's manifest + sha256
.venv/bin/python src/consult.py "<situation>"  # KEYLESS precedent lookup (Step 1)

# --- these need an LLM key in .env ---
.venv/bin/python src/consult.py --map "<situation>"   # Step 2: tailored playbook
.venv/bin/python scripts/throttled_build.py --prune   # build all 40 (rate-limit friendly)
.venv/bin/python src/mesh.py publish         # export pack/tessera-<v>.mempack
.venv/bin/python src/mesh.py install         # install into Cognee (round-trip / contrast demo)
.venv/bin/python src/query.py "<situation>"  # bare-LLM vs Cognee-recall contrast
.venv/bin/python src/consult_server.py       # Mosaic Console at http://localhost:8000
.venv/bin/python src/mesh.py uninstall       # forget an installed pack — the reversibility beat
```

## Connect via MCP (the primary path)

In production, analysts never open the Console — their existing agent calls the Node's one
MCP tool, `consult_pack(situation, map_to_situation)`, and weaves the precedent (with
citations) into its own answer. The tool description is plain and factual, so the host agent
does not auto-invoke it; consulting is user-initiated. Point any MCP client at
`src/mcp_server.py`:

```jsonc
// e.g. Claude Desktop  ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "mosaic-tessera": {
      "command": "/ABSOLUTE/PATH/mosaic/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/mosaic/src/mcp_server.py"]
    }
  }
}
```

The first call returns the precedent, its shared warning signs, and an invitation to map it.
On the user's confirmation, the agent calls again with `map_to_situation=True` and the **full
enriched situation** to get the tailored playbook.

## Try it on a fresh machine — no LLM key

Portability is the whole point: you **download** the pack, you don't rebuild it. Step 1 (the
closest precedent + warning signs + citations) runs entirely locally with fastembed — **no
LLM API key, no Cognee install.**

```bash
git clone https://github.com/dhruvaviya06/mosaic-memorypack && cd mosaic-memorypack
python -m venv .venv && .venv/bin/pip install -r requirements.txt
# download the built pack from GitHub Releases into pack/ :
curl -L -o pack/tessera-0.1.0.mempack \
  https://github.com/dhruvaviya06/mosaic-memorypack/releases/latest/download/tessera-0.1.0.mempack
# keyless precedent lookup — no key needed:
.venv/bin/python src/consult.py "a family office with concentrated leveraged swaps and margin breaches"
```

Want the playbook tailored to your situation (Step 2)? Add an LLM key to `.env` and re-run
with `--map`:

```bash
.venv/bin/python src/consult.py --map "a family office with concentrated leveraged swaps and margin breaches"
```

## Build your own pack

Rebuilding from source proves *reproducibility* (and is how you author a new pack). This
needs an LLM key — Cognee's graph extraction runs the model:

```bash
cp .env.example .env                                  # paste one LLM key (Groq/Gemini/OpenAI)
.venv/bin/python scripts/throttled_build.py --prune   # build all 40 (rate-limit friendly, resumable)
.venv/bin/python src/mesh.py publish                  # export pack/tessera-<v>.mempack (incl. cases.json)
.venv/bin/python src/mesh.py install                  # install into Cognee (round-trip / contrast demo)
.venv/bin/python src/consult_server.py                # Console at http://localhost:8000
```

Then attach the resulting `pack/tessera-<v>.mempack` to a **GitHub Release** so fresh Nodes
can download it (see the keyless quickstart above).

## Repo layout

```
sources/       raw primary-source docs (the evidence layer)
cases/         seven-field curated JSON (the expertise layer) — 40 cases
ontology/      tessera.owl
src/           validate / build / export / import / query / keyless / consult / learn
               (keyless.py = local no-LLM retrieval; consult.py = keyless terminal consult)
scripts/       throttled_build.py — resumable, rate-limit-friendly build for free tiers
pack/          built .mempack artifacts
docs/          static Mosaic project splash (GitHub Pages)
SOURCES_INDEX.md   umbrella-doc → case mapping (provenance reference)
```

*Built for "The Hangover Part AI: Where's My Context?" — WeMakeDevs × Cognee.*
