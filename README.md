# Nebius Token Factory — AI Agent Skills

A collection of agent skills for [Claude](https://claude.ai) (and compatible AI coding assistants) that cover the full MLOps lifecycle on [Nebius Token Factory](https://tokenfactory.nebius.com) — fine-tuning, deployment, batch inference, and observability.

Each skill is a `SKILL.md` file loaded into an AI agent's context, giving it precise knowledge of Nebius APIs, correct endpoints, and working code patterns.

Run this command to start using the skills:

```bash
npx skills add github.com/Arindam200/nebius-skills
```


## Skills

| Skill | What it does |
|-------|-------------|
| [`nebius-finetune`](./skills/nebius-finetune/SKILL.md) | Upload datasets, create LoRA / full fine-tuning jobs, monitor training, download checkpoints |
| [`nebius-deploy-lora`](./skills/nebius-deploy-lora/SKILL.md) | Deploy a fine-tuned LoRA adapter as a serverless endpoint — from a Nebius job or HuggingFace |
| [`nebius-dedicated-endpoint`](./skills/nebius-dedicated-endpoint/SKILL.md) | Create isolated GPU-backed endpoints, configure autoscaling, run inference, tear down |
| [`nebius-batch-synthetic`](./skills/nebius-batch-synthetic/SKILL.md) | Run async batch inference at 50% cheaper cost — ideal for synthetic dataset generation |
| [`nebius-observability`](./skills/nebius-observability/SKILL.md) | Query Prometheus metrics, set up Grafana, run PromQL against Token Factory inference |
| [`nebius-datalab-pipeline`](./skills/nebius-datalab-pipeline/SKILL.md) | Full 8-step end-to-end MLOps pipeline: seed prompts → teacher distillation → fine-tune → deploy |

---

## Quickstart

### Install a skill in Cursor

1. Clone this repo:
   ```bash
   git clone https://github.com/Arindam200/nebius-skills.git
   ```
2. In Cursor, open **Settings → Features → Cursor Skills** and add the path to a `SKILL.md` file — e.g., `nebius-skills/skills/nebius-finetune/SKILL.md`.
3. The skill is now active. Ask Claude anything about fine-tuning on Nebius and it will automatically load the skill.

### Use the companion scripts

The [`scripts/`](./scripts/) folder contains standalone Python scripts that mirror each skill's workflow — useful for testing, automation, or as a reference.

```bash
cd scripts
pip install -r requirements.txt
export NEBIUS_API_KEY="your-key"
export NEBIUS_PROJECT_ID="your-project-id"   # required for observability only

python 01_finetuning.py
python 02_dedicated_endpoints.py
python 03_observability.py
python 04_post_training_deploy.py
python 05_batch_inference_synthetic.py
python 06_datalab_e2e_workflow.py            # full end-to-end pipeline
```

---

## Repository Structure

```
nebius-skills/
├── README.md
├── .gitignore
│
├── skills/                              ← installable AI agent skills
│   ├── nebius-finetune/
│   │   └── SKILL.md
│   ├── nebius-deploy-lora/
│   │   └── SKILL.md
│   ├── nebius-dedicated-endpoint/
│   │   └── SKILL.md
│   ├── nebius-batch-synthetic/
│   │   └── SKILL.md
│   ├── nebius-observability/
│   │   └── SKILL.md
│   └── nebius-datalab-pipeline/
│       └── SKILL.md
│
├── scripts/                             ← companion Python scripts
│   ├── README.md
│   ├── requirements.txt
│   ├── 01_finetuning.py
│   ├── 02_dedicated_endpoints.py
│   ├── 03_observability.py
│   ├── 04_post_training_deploy.py
│   ├── 05_batch_inference_synthetic.py
│   └── 06_datalab_e2e_workflow.py
│
└── evals/                               ← skill quality benchmarks
    ├── README.md
    ├── evals.json
    ├── evals_with_assertions.json
    └── iteration-1/
        ├── benchmark.json
        ├── benchmark.md
        └── eval-{N}-{name}/
            ├── eval_metadata.json
            ├── with_skill/
            └── without_skill/
```

---

## Skills Deep-Dive

### nebius-finetune

Fine-tune foundation models using the OpenAI-compatible API.

**Trigger phrases:** "fine-tune on Nebius", "train a model with my dataset", "start a LoRA fine-tuning job"

**Supported models:** `Meta-Llama-3.1-8B-Instruct`, `Llama-3.3-70B-Instruct`

**Key hyperparameters:**

| Parameter | Default | Notes |
|-----------|---------|-------|
| `n_epochs` | 3 | Training passes |
| `learning_rate_multiplier` | 2e-5 | |
| `lora_rank` | 16 | Omit for full fine-tuning |

**Reference script:** `scripts/01_finetuning.py` · [Docs](https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune)

---

### nebius-deploy-lora

Serve a fine-tuned LoRA adapter as a serverless endpoint with per-token billing.

**Trigger phrases:** "deploy my fine-tuned model", "serve my LoRA adapter", "deploy from HuggingFace"

**Two deployment paths:**
- **From a Nebius fine-tuning job** — use `{job_id}:{checkpoint_id}` as the source
- **From HuggingFace** — pass the HF URL directly as `source`, no file upload needed

**Reference script:** `scripts/04_post_training_deploy.py` · [Docs](https://docs.tokenfactory.nebius.com/post-training/deploy-custom-model)

---

### nebius-dedicated-endpoint

Isolated, GPU-backed deployments with per-region data residency and autoscaling.

**Trigger phrases:** "create a dedicated endpoint", "deploy a model on dedicated GPU", "set up autoscaling"

**Regional inference URLs:**

| Region | Base URL |
|--------|----------|
| eu-north1 | `https://api.tokenfactory.nebius.com/v1/` |
| eu-west1 | `https://api.tokenfactory.eu-west1.nebius.com/v1/` |
| us-central1 | `https://api.tokenfactory.us-central1.nebius.com/v1/` |

**Reference script:** `scripts/02_dedicated_endpoints.py` · [Docs](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints)

---

### nebius-batch-synthetic

Async LLM batch inference at 50% cheaper than real-time, no rate-limit impact.

**Trigger phrases:** "run batch inference", "generate synthetic training data", "batch job on Token Factory"

**Limits:**

| Constraint | Value |
|------------|-------|
| Max requests / file | 5,000,000 |
| Max file size | 10 GB |
| Completion window | 24 hours |
| Cost vs real-time | **50% cheaper** |

**Reference script:** `scripts/05_batch_inference_synthetic.py` · [Docs](https://docs.tokenfactory.nebius.com/ai-models-inference/batch-inference)

---

### nebius-observability

Real-time and historical inference metrics via a Prometheus-compatible API.

**Trigger phrases:** "get Nebius metrics", "set up Prometheus for Token Factory", "connect Grafana to Nebius"

**Metrics endpoint:**
```
https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/metrics
```

**Key metrics:** `nebius_requests_total`, `nebius_time_to_first_token_ms_bucket`, `nebius_errors_total`, `nebius_active_replicas`

**Reference script:** `scripts/03_observability.py` · [Docs](https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations)

---

### nebius-datalab-pipeline

Orchestrates the complete MLOps loop across all Nebius services.

**Trigger phrases:** "full Nebius pipeline", "data flywheel", "teacher distillation pipeline", "end-to-end fine-tuning on Nebius"

**The 8-step pipeline:**

```
Seed prompts
    → Generate inference logs (chat completions → auto-stored in DataLab)
    → Upload raw dataset
    → Batch inference with teacher model (70B)
    → Curate outputs (quality filter)
    → Upload curated training file
    → Fine-tune student model (8B LoRA)
    → Deploy LoRA adapter
    → Smoke test
```

**Reference script:** `scripts/06_datalab_e2e_workflow.py` · [Docs](https://docs.tokenfactory.nebius.com/data-lab/overview)

---

## Skill Cross-Reference

```
nebius-datalab-pipeline
    ├── uses → nebius-batch-synthetic   (step 3: teacher model inference)
    ├── uses → nebius-finetune          (step 6: train student model)
    ├── uses → nebius-deploy-lora       (step 7: serve the result)
    ├── uses → nebius-observability     (monitor inference quality)
    └── uses → nebius-dedicated-endpoint (alternative serving path)

nebius-finetune
    └── next → nebius-deploy-lora       (after job.status == "succeeded")
```

---

## Benchmark Results (Iteration 1)

Skills were tested against 9 real-user prompts, each run with and without the skill loaded. Full data in [`evals/iteration-1/benchmark.md`](./evals/iteration-1/benchmark.md).

| Configuration | Mean Pass Rate |
|---------------|---------------|
| With skill (skill loaded) | **96.7%** |
| Without skill (baseline) | 58.5% |
| Delta | **+38.2pp** |

3 of 9 evals had skill loading failures (trigger reliability issue, not content). Content quality when loaded: 96.7%.

---

## Prerequisites

```bash
pip install openai requests pyyaml
export NEBIUS_API_KEY="your-key"
```

API base: `https://api.tokenfactory.nebius.com/v1/`

---

## Contributing

Pull requests are welcome. To add or improve a skill:

1. Edit the relevant `skills/<name>/SKILL.md`
2. Run the eval set in `evals/evals_with_assertions.json` against your changes
3. Add results to a new `evals/iteration-N/` directory
4. Open a PR with benchmark delta

See [`evals/README.md`](./evals/README.md) for the eval workflow.

---

## License

MIT
