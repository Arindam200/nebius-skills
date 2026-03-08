# Benchmark — nebius-skills — Iteration 1

Generated: 2026-03-08

---

## Summary

| Configuration | Mean Pass Rate | Evals |
|---------------|---------------|-------|
| **with_skill** (all) | **68.9%** | 9 evals |
| **with_skill** (skill loaded only) | **96.7%** | 6/9 evals |
| **without_skill** | **58.5%** | 8/9 evals (1 missing) |
| **Delta (overall)** | **+10.4pp** | |
| **Delta (loaded only)** | **+38.2pp** | |

> ⚠️ 3 of 9 evals had **skill loading failures** — the skill was not triggered/loaded by the agent. When those are excluded, the skill performs at 96.7% vs 58.5% baseline (+38.2pp). Fixing loading is the top priority for iteration-2.

---

## Per-Eval Results

| # | Eval Name | Skill | With Skill | Without Skill | Delta | Skill Loaded? |
|---|-----------|-------|-----------|--------------|-------|--------------|
| 0 | finetune-upload-and-start | nebius-finetune | **100%** (5/5) | 40% (2/5) | **+60pp** | ✅ |
| 1 | finetune-monitor-checkpoints | nebius-finetune | **100%** (5/5) | 80% (4/5) | **+20pp** | ✅ |
| 2 | dedicated-create-and-infer | nebius-dedicated-endpoint | **100%** (6/6) | — (missing) | — | ✅ |
| 3 | dedicated-patch-scaling | nebius-dedicated-endpoint | 100% (4/4) | 100% (4/4) | 0pp | ✅ |
| 4 | observability-grafana-promql | nebius-observability | 40% (2/5) | 40% (2/5) | 0pp | ❌ failed |
| 5 | observability-prometheus-config | nebius-observability | **80%** (4/5) | 40% (2/5) | **+40pp** | ✅ |
| 6 | deploy-lora-from-job | nebius-deploy-lora | 0% (0/5) | 60% (3/5) | **−60pp** | ❌ failed |
| 7 | deploy-lora-from-hf | nebius-deploy-lora | **100%** (4/4) | 25% (1/4) | **+75pp** | ✅ |
| 8 | batch-10k-questions | nebius-batch-synthetic | 0% (0/6) | 83% (5/6) | **−83pp** | ❌ failed |

---

## Assertion-Level Breakdown

### eval-0 — finetune-upload-and-start

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Uses correct Nebius base_url | ✅ | ❌ (used api.studio.nebius.ai instead) |
| Uses OpenAI client for fine-tuning | ✅ | ❌ (used raw curl) |
| Uploads file with purpose='fine-tune' | ✅ | ✅ |
| Creates job with lora_rank | ✅ | ❌ (no lora_rank) |
| Specifies correct base model | ✅ | ✅ |

### eval-1 — finetune-monitor-checkpoints

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Uses list_events to poll | ✅ | ✅ |
| Checks status for 'succeeded' | ✅ | ✅ |
| Uses checkpoints.list | ✅ | ✅ |
| Downloads via files.content | ✅ | ❌ (used retrieve_content — wrong method) |
| References job ID ftjob-abc123 | ✅ | ✅ |

### eval-3 — dedicated-patch-scaling

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Uses PATCH method | ✅ | ✅ |
| Uses correct endpoint URL | ✅ | ✅ |
| Sets max_replicas to 8 | ✅ | ✅ |
| Mentions no downtime | ✅ | ✅ |

### eval-5 — observability-prometheus-config

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Complete prometheus.yml with scrape_configs | ✅ | ✅ |
| Includes /prometheus/metrics metrics_path | ❌ (used federate path) | ❌ (used /metrics) |
| Mentions PROJECT_ID in metrics path | ✅ | ❌ |
| Uses bearer_token auth | ✅ | ✅ |
| Recommends 15s scrape interval | ✅ | ❌ (used 60s) |

### eval-6 — deploy-lora-from-job (SKILL LOADING FAILURE)

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Uses POST /v0/models | ❌ (no response) | ❌ (used wrong SDK/URL) |
| Uses ftjob-xyz789 in source | ❌ (no response) | ✅ |
| Retrieves latest checkpoint | ❌ (no response) | ❌ (no checkpoint step) |
| Polls for status == 'active' | ❌ (no response) | ✅ (uppercase ACTIVE) |
| Shows inference with deployed model | ❌ (no response) | ✅ |

### eval-7 — deploy-lora-from-hf

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Uses HuggingFace URL as source field | ✅ | ❌ |
| Uses POST /v0/models | ✅ | ❌ (wrong base URL) |
| Specifies base_model as Llama 3.1 8B | ✅ | ✅ |
| Wait-for-validation polling loop | ✅ | ❌ (no polling) |

### eval-8 — batch-10k-questions (SKILL LOADING FAILURE)

| Assertion | With Skill | Without Skill |
|-----------|-----------|--------------|
| Mentions 50% cost reduction | ❌ (no response) | ❌ |
| Builds JSONL with custom_id | ❌ (no response) | ✅ |
| Uploads with purpose='batch' | ❌ (no response) | ✅ |
| Creates batch with completion_window='24h' | ❌ (no response) | ✅ |
| Downloads via output_file_id | ❌ (no response) | ✅ |
| Uses Llama 70B | ❌ (no response) | ✅ |

---

## Analyst Observations

### 🔴 Critical: 3 Skill Loading Failures

Skills `nebius-observability` (eval-4), `nebius-deploy-lora` (eval-6), and `nebius-batch-synthetic` (eval-8) failed to load in the with_skill runs. This is a **triggering/description problem**, not a content problem — when the skills did load (eval-5, eval-7), they performed well.

**Fix:** Run `scripts/run_loop.py` description optimization on these three skills. Their descriptions may not be "pushy" enough to trigger loading for the specific phrasings in those eval prompts.

### 🟡 Non-Discriminating Eval: dedicated-patch-scaling (eval-3)

Both runs scored 100%. The task is too straightforward — Claude answers it correctly without the skill. Consider replacing with a harder variant (e.g., multi-region endpoint + flavor change) in iteration-2.

### 🟢 Strong Signal When Loaded

The three evals where the skill clearly made a difference:
- **+75pp** on deploy-lora-from-hf (without skill: used wrong URL, no polling loop)
- **+60pp** on finetune-upload-and-start (without skill: wrong base URL, raw curl instead of OpenAI client)
- **+40pp** on observability-prometheus-config (without skill: wrong scrape interval, no PROJECT_ID)

### ⚪ Missing Data

- **eval-2 without_skill**: baseline agent was still pending at grading time — delta is unknown.
- **All timing.json files**: token counts and duration were not captured during iteration-1. Record these in iteration-2 via subagent notification data.

---

## What to Fix in Iteration-2

1. **Fix skill loading for:** `nebius-observability`, `nebius-deploy-lora`, `nebius-batch-synthetic`
   - Run description optimization (`scripts/run_loop.py`) on all three
2. **Re-run eval-2 without_skill** baseline (response was missing)
3. **Replace or harden eval-3** — it is not discriminating
4. **Capture timing data** — save `timing.json` immediately when each subagent task completes
