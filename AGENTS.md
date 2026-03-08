# AGENTS.md — Nebius Skills Repo

Instructions for AI agents (Codex, Claude, Cursor, etc.) working in this repository.

## What this repo is

A collection of AI agent skills (`SKILL.md` files) for Nebius Token Factory. Each skill gives AI assistants precise knowledge of Nebius-specific APIs, endpoints, and code patterns that they would otherwise hallucinate or get wrong.

## Repo layout

```
skills/          ← the SKILL.md files — this is the primary artifact of this repo
scripts/         ← companion Python scripts, one per skill workflow
evals/           ← benchmark data: test prompts, grading results, iteration history
```

## Rules for editing skills (`skills/*/SKILL.md`)

- The YAML frontmatter `description:` field is the trigger mechanism — it determines when an AI assistant loads the skill. Keep it specific and include concrete Nebius trigger phrases.
- API base URL is always `https://api.tokenfactory.nebius.com/v1/` for data plane. Control plane is `https://api.tokenfactory.nebius.com` (no `/v1/`).
- The `v0/` prefix is correct for dedicated endpoints and custom model deploy (`/v0/dedicated_endpoints`, `/v0/models`). Do not change these to `/v1/`.
- Script references use the path `scripts/<filename>.py` — not `nebius-scripts/`.
- Keep each SKILL.md under 500 lines. If content grows beyond that, move reference material to a `references/` subdirectory within that skill folder.

## Rules for editing scripts (`scripts/*.py`)

- Scripts are numbered `01_` through `06_` and correspond 1:1 with skills. Do not renumber.
- Each script must work standalone — set config via environment variables (`NEBIUS_API_KEY`, `NEBIUS_PROJECT_ID`) at the top, no CLI arg parsing.
- All scripts use `openai` Python SDK with `base_url="https://api.tokenfactory.nebius.com/v1/"` — never `api.studio.nebius.ai`.
- The `requests` library is used directly (not `openai`) for control plane calls (`/v0/dedicated_endpoints`, `/v0/models`).

## Rules for editing evals (`evals/`)

- `evals.json` and `evals_with_assertions.json` are the source of truth for test cases. Edit these to add/modify eval prompts.
- Each benchmark iteration lives in its own `evals/iteration-N/` directory. Never overwrite a previous iteration — always create a new one.
- `grading.json` files use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details`).
- `timing.json` fields: `total_tokens`, `duration_ms`, `total_duration_seconds`.

## Key Nebius API facts to never get wrong

| Fact | Correct value |
|------|--------------|
| Data plane base URL | `https://api.tokenfactory.nebius.com/v1/` |
| Fine-tuning SDK | OpenAI Python client with custom `base_url` |
| LoRA deploy endpoint | `POST /v0/models` |
| Dedicated endpoint create | `POST /v0/dedicated_endpoints` |
| Monitoring URL | `https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/metrics` |
| Batch file purpose | `"batch"` (not `"fine-tune"`) |
| Fine-tune file purpose | `"fine-tune"` |
| eu-west1 inference URL | `https://api.tokenfactory.eu-west1.nebius.com/v1/` |
| us-central1 inference URL | `https://api.tokenfactory.us-central1.nebius.com/v1/` |

## What NOT to do

- Do not use `api.studio.nebius.ai` — this is the old/wrong URL.
- Do not invent Nebius SDK methods. The only SDK used is the standard OpenAI Python client pointed at the Nebius base URL.
- Do not commit `.jsonl` files, `.safetensors`, `.tar.gz`, or any file matching `.env*`.
- Do not modify `evals/iteration-1/` — it is a historical benchmark record.
- Do not add dependencies beyond `openai`, `requests`, `pyyaml` in `scripts/requirements.txt` without a clear reason.
