# CLAUDE.md — Nebius Skills Repo

Context for Claude when working in this repository.

## What this is

This repo contains AI agent skills for Nebius Token Factory — a platform for LLM fine-tuning, deployment, and inference. Each skill is a `SKILL.md` file that gets loaded into Claude's context to give it accurate Nebius API knowledge.

The skills exist because Claude (and other LLMs) frequently hallucinate wrong URLs, SDK calls, and endpoint paths for Nebius. With these skills loaded, accuracy on Nebius tasks goes from ~58% to ~97%.

## Folder purposes at a glance

| Folder | What it is | Modify? |
|--------|-----------|---------|
| `skills/` | The SKILL.md files — main deliverable | Yes |
| `scripts/` | Python scripts mirroring each skill | Yes |
| `evals/` | Benchmark data and test prompts | Add iterations only |

## Critical API details — do not get these wrong

**Base URLs:**
- Data plane (inference, fine-tuning): `https://api.tokenfactory.nebius.com/v1/`
- Control plane (endpoints, custom models): `https://api.tokenfactory.nebius.com` (no `/v1/`)
- Monitoring: `https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/...`
- eu-west1 inference: `https://api.tokenfactory.eu-west1.nebius.com/v1/`
- us-central1 inference: `https://api.tokenfactory.us-central1.nebius.com/v1/`

**Never use** `api.studio.nebius.ai` — that is an outdated URL that no longer works.

**SDK pattern** — always use the OpenAI Python client with `base_url`:
```python
from openai import OpenAI
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=os.environ["NEBIUS_API_KEY"])
```

**Control plane calls** use `requests` directly (not the OpenAI client):
```python
requests.post("https://api.tokenfactory.nebius.com/v0/dedicated_endpoints", headers=..., json=...)
requests.post("https://api.tokenfactory.nebius.com/v0/models", headers=..., json=...)
```

**Key Nebius-specific fields** that Claude often misses:
- `lora_rank` in fine-tuning hyperparameters (e.g. `"lora_rank": 16`)
- `routing_key` for dedicated endpoint inference (returned at creation, used as model name)
- `source` field in LoRA deploy: either `"{job_id}:{checkpoint_id}"` or a HuggingFace URL
- `completion_window="24h"` when creating batch jobs
- `purpose="batch"` (not `"fine-tune"`) for batch inference file uploads

## Skill file conventions

- YAML frontmatter with `name:` and `description:` is required in every `SKILL.md`
- `description:` is the trigger — it must include concrete Nebius phrases that match what users actually type
- Script references in skills use `scripts/<filename>.py` (not `nebius-scripts/`)
- Keep SKILL.md under 500 lines; overflow goes in `references/` inside the skill folder

## Eval conventions

When adding a new benchmark iteration:
- Create `evals/iteration-N/` (never edit `iteration-1/`)
- Each eval dir needs `eval_metadata.json`, `with_skill/`, `without_skill/`
- `grading.json` fields are `text`, `passed`, `evidence`
- Save `timing.json` immediately when subagent tasks complete (data is only available in the completion notification)

## What the skills cover

| Skill | Covers |
|-------|--------|
| `nebius-finetune` | Dataset upload, LoRA/full fine-tuning jobs, polling, checkpoint download |
| `nebius-deploy-lora` | Serverless LoRA deployment from job or HuggingFace, polling for active status |
| `nebius-dedicated-endpoint` | Dedicated GPU endpoints, templates, flavors, autoscaling, regional inference |
| `nebius-batch-synthetic` | Async batch inference, JSONL format, cost advantage, synthetic data export |
| `nebius-observability` | Prometheus metrics, PromQL queries, Grafana datasource config |
| `nebius-datalab-pipeline` | Full 8-step pipeline: seed → teacher inference → curate → fine-tune → deploy → test |

## Things to avoid

- Do not invent Nebius Python SDK methods — there is no official Nebius SDK; everything goes through the OpenAI client or raw `requests`
- Do not commit `.jsonl`, `.safetensors`, `.tar.gz`, or `.env*` files (see `.gitignore`)
- Do not overwrite `evals/iteration-1/` — it is a fixed historical record
- Do not change the `v0/` prefix on `/v0/dedicated_endpoints` or `/v0/models` — those are intentionally different from the `/v1/` data plane
