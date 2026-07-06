# Mosaic — RiskLore

> **Mosaic is the marketplace; RiskLore is its first verified pack.**

A marketplace where organizations trade **verified experience** instead of models or raw
data. Expert knowledge is curated into portable **memory packs** — a JSON knowledge graph +
ontology + provenance manifest + a signed `pack.json`, deliberately containing **no
embeddings** so a pack stays model-agnostic. A pack is published to a registry and installed
by any organization into its own self-hosted **Node** (a Cognee instance), where Cognee
**re-embeds it locally** and mounts it as a read-only, cleanly removable dataset. The org's
existing AI agent queries it via one MCP tool — gaining citable precedent with a full
evidence trail to primary sources, and **zero workflow change**.

**RiskLore v0.1** is the flagship pack: the causal anatomy of financial failures and fraud
typologies, distilled from free regulatory and judicial primary sources.

> *Instead of sharing customer data, organizations share analyst expertise.*

---

## Cognee's four verbs, operating *between* organizations instead of within one

| Marketplace action | Cognee lifecycle |
|--------------------|------------------|
| publish            | `remember` + `improve` |
| consume            | `recall` (via `consult_risklore`) |
| maintain (feedback)| `improve` |
| expire / uninstall | `forget` |

## The three products every script serves

1. **The Registry** (we host) — publish, discover, hash-verify, version packs like npm.
   → `export_pack.py`, `pack/` artifacts, `registry-ui/`.
2. **The Node** (orgs run) — Cognee + install/uninstall tooling + MCP server. `install → verify
   sha256 → mount isolated dataset → re-embed locally`. Uninstall = one `forget()`.
   → `import_pack.py`, `test_roundtrip.py`.
3. **The MCP endpoint** — one tool, `consult_risklore(situation)`, that the org's *existing*
   agent calls. We ship no chat UI, no agent, no LLM. → `query.py` / `consult()`.

*Decision support only — human judgment is final.*

---

## What's built

- **RiskLore pack** — 6 deep, primary-source-grounded cases (Archegos, SVB, PNB/Nirav Modi,
  Yes Bank, IL&FS, DHFL) + 30 fraud/AML typologies. Built graph: **84 nodes / 151 edges**
  for the deep tier, with real causal relations (`defaulted_on_margin_calls_on`,
  `imposed_moratorium_on`, `had_concentrated_positions_in`, `interconnected_with`).
- **Round-trip proven** — `recall → export → forget → import → recall`: knowledge crosses a
  fresh Cognee instance with **zero embeddings shipped** and a verified sha256 seal.
- **Contrast demo** — the same situation answered by a bare LLM (generic checklist) vs the
  pack-backed agent (names the Archegos precedent + concrete investigation steps).
- **Provenance** — every deep case's `source_documents` resolves to a real regulatory/judicial
  document in `sources/`.

## Pack format (`risklore-{version}.mempack`)

A gzipped tarball, **no embeddings**:
- `graph.json` — node/edge lists (`id, type, name, text, source_ref`)
- `risklore.owl` — ontology (7 classes / 6 relations)
- `provenance.json` — case → institution / year / source documents
- `pack.json` — manifest: platform, name, version, publisher, license, verification tier,
  node/edge counts, and a **sha256 content hash** (tamper seal)

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
cp .env.example .env      # then paste a free Groq key (console.groq.com) into .env
```

## Run

```bash
# --- no LLM needed (safe to run anytime) ---
.venv/bin/python src/validate_cases.py     # check case files against the schema
.venv/bin/python src/mesh.py info          # show the built pack's manifest + sha256

# --- these drive Cognee (need an LLM key in .env) ---
.venv/bin/python src/build_memory.py       # build the deep-tier pack (add --all for typologies)
.venv/bin/python src/inspect_graph.py      # X-ray the graph (--html for an interactive view)
.venv/bin/python src/mesh.py publish       # export pack/risklore-<v>.mempack
.venv/bin/python src/mesh.py install       # install the pack into a fresh dataset (re-embeds locally)
.venv/bin/python src/test_roundtrip.py     # prove portability across instances
.venv/bin/python src/query.py "<situation>"  # bare-LLM vs pack contrast (consult_risklore)
.venv/bin/python src/mesh.py uninstall     # forget an installed pack — the reversibility beat
```

## Deploy (registry UI)

The registry is a self-contained static page (`registry-ui/index.html`, mirrored to
`docs/index.html` for hosting). To publish it as your deployed link, enable GitHub Pages once:
**Settings → Pages → Source: Deploy from a branch → `main` / `docs`**. Deployed link:
`https://<user>.github.io/<repo>/` (e.g. `https://dhruvaviya06.github.io/mosaic/`).

## Repo layout

```
sources/       raw primary-source docs (the evidence layer)
cases/         seven-field curated JSON (the expertise layer)
ontology/      risklore.owl
src/           validate / build / inspect / export / import / roundtrip / query
pack/          built .mempack artifacts
registry-ui/   Mosaic registry stub (deployable static site)
SOURCES_INDEX.md   umbrella-doc → case mapping (provenance reference)
```

*Built for "The Hangover Part AI: Where's My Context?" — WeMakeDevs × Cognee.*
