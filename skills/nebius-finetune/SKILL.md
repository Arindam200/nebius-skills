---
name: nebius-finetune
description: Fine-tune a model on Nebius Token Factory. Use this skill whenever the user wants to train, fine-tune, or adapt a model on Nebius — including uploading training data, creating a fine-tuning job, monitoring training progress, or downloading model checkpoints. Trigger for phrases like "fine-tune on Nebius", "train a model with my dataset", "start a Nebius fine-tuning job", "LoRA fine-tune", "check my training job status", or any question about supervised fine-tuning workflows on Token Factory.
---

# Nebius Fine-Tuning

Fine-tune foundation models (LoRA or full weights) on Nebius Token Factory using the OpenAI-compatible API.

## Prerequisites

```bash
pip install openai
export NEBIUS_API_KEY="your-key"
```

API base: `https://api.tokenfactory.nebius.com/v1/`

## Supported base models

Key deployable models:
- `meta-llama/Meta-Llama-3.1-8B-Instruct` — LoRA + full fine-tuning, LoRA deployable serverlessly
- `meta-llama/Llama-3.3-70B-Instruct` — LoRA fine-tuning, LoRA deployable serverlessly

Full model list: https://docs.tokenfactory.nebius.com/post-training/models

## Dataset formats

Upload `.jsonl` files (max 5 GB). Supported types:

**Conversational** (most common):
```jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

**Instruction**:
```jsonl
{"prompt": "Question here", "completion": "Answer here"}
```

## Complete workflow

### 1. Upload datasets

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=API_KEY)

training_file = client.files.create(file=open("training.jsonl", "rb"), purpose="fine-tune")
# Optional validation:
validation_file = client.files.create(file=open("validation.jsonl", "rb"), purpose="fine-tune")
```

### 2. Create fine-tuning job

```python
job = client.fine_tuning.jobs.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    training_file=training_file.id,
    hyperparameters={
        "n_epochs": 3,
        "learning_rate_multiplier": 2e-5,
        "lora_rank": 16,          # omit for full fine-tuning
    },
)
print(f"Job: {job.id}  status={job.status}")
```

### 3. Monitor job

Status progression: `validating_files → queued → running → succeeded / failed`

```python
import time
while True:
    job = client.fine_tuning.jobs.retrieve(job_id)
    events = client.fine_tuning.jobs.list_events(job_id, limit=20).data
    for ev in reversed(events):
        print(f"[{ev.created_at}] {ev.message}")
    print(f"status={job.status}  trained_tokens={job.trained_tokens}")
    if job.status in ("succeeded", "failed", "cancelled"):
        break
    time.sleep(30)
```

### 4. Download checkpoints

```python
import os
checkpoints = client.fine_tuning.jobs.checkpoints.list(job_id).data
for ckpt in checkpoints:
    os.makedirs(ckpt.id, exist_ok=True)
    for file_id in ckpt.result_files:
        file_obj = client.files.retrieve(file_id)
        content  = client.files.content(file_id)
        out_path = os.path.join(ckpt.id, os.path.basename(file_obj.filename))
        content.write_to_file(out_path)
        print(f"Saved: {out_path}")
```

## Key hyperparameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `n_epochs` | 3 | Number of training passes |
| `learning_rate_multiplier` | 2e-5 | Scale relative to base LR |
| `lora_rank` | 16 | LoRA rank; omit for full fine-tuning |
| `context_length` | model default | Max sequence length |

## Packing (recommended for short samples)

Add `"packing": true` to hyperparameters to bin-pack short samples — gives more stable gradients and better compute efficiency. Attention is masked across segment boundaries so samples never interact.

## After training

Once `status=succeeded`, use the checkpoint to:
- Deploy as a serverless LoRA adapter → see **nebius-deploy-lora** skill
- Run batch evaluation → see **nebius-batch-synthetic** skill

## Bundled reference

Read `references/api-spec.md` when the user asks about hyperparameter details, API field specs, checkpoint structure, or dataset requirements.

## Reference script

Full working script: `scripts/01_finetuning.py`

Docs: https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune
