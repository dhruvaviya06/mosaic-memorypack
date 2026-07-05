# Memory Mesh — RiskLore

> **Memory Mesh is the marketplace; RiskLore is its first verified pack.**

A marketplace where organizations trade **verified experience** instead of models or raw
data. Knowledge is curated into portable **memory packs** — a JSON knowledge graph +
ontology + provenance manifest + signed `pack.json`, deliberately containing **no
embeddings** so packs stay model-agnostic. A pack is published to a registry and installed
by any organization into its own self-hosted **Node** (a Cognee instance), where Cognee
re-embeds and enriches it locally and mounts it as a read-only, cleanly removable dataset.

**RiskLore v1.0** is the flagship pack: the causal anatomy of historical financial failures,
distilled entirely from free regulatory and judicial primary sources.

### Cognee's four verbs, operating *between* organizations instead of within one
| Marketplace action | Cognee lifecycle |
|--------------------|------------------|
| publish            | `remember` + `improve` |
| consume            | `recall` |
| maintain (feedback)| `improve` |
| expire / uninstall | `forget` |

---

## Status
🚧 Hackathon build in progress — *The Hangover Part AI: Where's My Context?* (WeMakeDevs × Cognee).
Phase 0 complete: repo scaffolded, self-hosted Cognee + Gemini stack verified.

## Stack
- **Cognee 1.2.2** (self-hosted: local LanceDB vector + Kuzu graph + SQLite)
- **Gemini** free tier for LLM + embeddings (via litellm)
- Python 3.14, isolated in `.venv/`

## Setup
```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env      # then paste your Google AI Studio key into .env
```

## Repo layout
```
sources/       raw case PDFs (the evidence layer)
cases/         seven-field curated JSON files (the expertise layer)
ontology/      risklore.owl
src/           pipeline: build / inspect / export / import / roundtrip / query
pack/          built .mempack artifacts
registry-ui/   Memory Mesh registry stub (RiskLore card + stub listings)
```
