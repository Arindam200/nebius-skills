---
name: nebius-datalab-pipeline
description: Full DataLab end-to-end pipeline on Nebius Token Factory — from raw inference logs through synthetic data generation, fine-tuning, and model deployment. Use this skill whenever the user wants to run a complete MLOps workflow on Nebius, combine DataLab with fine-tuning, do teacher-student distillation at scale, build a data flywheel, automate the path from prompts to a deployed custom model, or orchestrate multiple Nebius services together. Trigger for phrases like "full Nebius pipeline", "DataLab workflow", "end-to-end fine-tuning on Nebius", "teacher distillation pipeline", "data flywheel", "automate Nebius training and deployment", or any question involving multiple Nebius services chained together.
---

# Nebius DataLab — End-to-End Pipeline

Orchestrate the full MLOps loop: inference logs → batch synthesis → curate → fine-tune → deploy → serve.

## What DataLab stores

| Data type | Source |
|-----------|--------|
| Inference Logs | Chat completions via API/Playground (unless Zero Data Retention) |
| Filtered Datasets | SQL queries over inference logs |
| Uploaded Datasets | Manual upload |
| Batch Inference Outputs | Results from batch jobs |
| Fine-tuning Outputs | Checkpoints + fine-tuned model artifacts |

## Prerequisites

```bash
pip install openai requests
export NEBIUS_API_KEY="your-key"
```

## The 8-step pipeline

For the full working implementation, see `scripts/06_datalab_e2e_workflow.py`.

---

### Step 1 — Generate inference logs

Run live chat completions against your domain topics. These are automatically stored as inference logs in DataLab.

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=API_KEY)

for topic in domain_topics:
    resp = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        messages=[{"role": "user", "content": topic}],
    )
    # logged automatically in DataLab
```

---

### Step 2 — Upload raw dataset to DataLab

Upload JSONL as a fine-tune file so it's accessible in DataLab for filtering/reuse.

```python
with open("raw_dataset.jsonl", "rb") as f:
    client.files.create(file=f, purpose="fine-tune")
```

---

### Step 3 — Batch inference with teacher model

Use a large teacher model to generate high-quality responses. See **nebius-batch-synthetic** skill for the full batch API.

```python
# Build JSONL with teacher model (e.g., 70B)
# Upload + create batch → poll → download outputs
```

Key: use `temperature: 0.6` and large `max_tokens` for rich training signal.

---

### Step 4 — Curate outputs

Filter by quality (min length, confidence) and convert to fine-tuning conversational format:

```python
for rec in batch_results:
    reply  = rec["response"]["body"]["choices"][0]["message"]["content"].strip()
    if len(reply) < 50:
        continue   # skip low-quality
    training_examples.append({
        "messages": [
            {"role": "user",      "content": original_prompt},
            {"role": "assistant", "content": reply},
        ]
    })
```

---

### Step 5 — Upload curated training file

```python
with open("curated_training.jsonl", "rb") as f:
    training_file = client.files.create(file=f, purpose="fine-tune")
```

---

### Step 6 — Launch fine-tuning

See **nebius-finetune** skill for full details.

```python
job = client.fine_tuning.jobs.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    training_file=training_file.id,
    hyperparameters={"n_epochs": 2, "lora_rank": 16},
)
# poll until job.status == "succeeded"
```

---

### Step 7 — Deploy fine-tuned LoRA

See **nebius-deploy-lora** skill for full details.

```python
import requests

checkpoints = client.fine_tuning.jobs.checkpoints.list(job.id).data
ckpt_id = checkpoints[-1].id

requests.post("https://api.tokenfactory.nebius.com/v0/models", json={
    "source":     f"{job.id}:{ckpt_id}",
    "base_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "name":       "my-domain-model-v1",
}, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
# poll until status == "active"
```

---

### Step 8 — Smoke test

```python
resp = client.chat.completions.create(
    model=deployed_model_name,
    messages=[{"role": "user", "content": "Test your domain knowledge..."}],
)
print(resp.choices[0].message.content)
```

---

## Skill cross-references

This pipeline combines all Nebius skills. For details on each step:

| Step | Skill |
|------|-------|
| Batch inference | **nebius-batch-synthetic** |
| Fine-tuning | **nebius-finetune** |
| Deploy LoRA | **nebius-deploy-lora** |
| Monitor inference | **nebius-observability** |
| Dedicated endpoint | **nebius-dedicated-endpoint** |

## Reference script

Full 8-step orchestrated pipeline: `scripts/06_datalab_e2e_workflow.py`

Docs:
- https://docs.tokenfactory.nebius.com/data-lab/overview
- https://docs.tokenfactory.nebius.com/data-lab/batch-inference
- https://docs.tokenfactory.nebius.com/data-lab/fine-tuning
