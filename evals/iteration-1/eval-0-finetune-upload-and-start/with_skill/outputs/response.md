# Fine-Tuning Llama 3.1 8B on Nebius Token Factory: Upload Data and Start a LoRA Job

## Prerequisites

```bash
pip install openai
export NEBIUS_API_KEY="your-key-here"
```

API base: `https://api.tokenfactory.nebius.com/v1/`

## Step 1: Format Your Dataset

Use the conversational JSONL format (one example per line):

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful customer support agent for Acme Corp."}, {"role": "user", "content": "How do I reset my password?"}, {"role": "assistant", "content": "To reset your password, go to the login page and click Forgot Password..."}]}
```

Split off ~50 examples as `validation.jsonl` to track held-out loss during training.

## Step 2: Upload the Dataset

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key="your-key-here",
)

training_file = client.files.create(file=open("training.jsonl", "rb"), purpose="fine-tune")
print(f"Training file ID: {training_file.id}")

validation_file = client.files.create(file=open("validation.jsonl", "rb"), purpose="fine-tune")
print(f"Validation file ID: {validation_file.id}")
```

## Step 3: Create the LoRA Fine-Tuning Job

```python
job = client.fine_tuning.jobs.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    training_file=training_file.id,
    validation_file=validation_file.id,
    hyperparameters={
        "n_epochs": 3,
        "learning_rate_multiplier": 2e-5,
        "lora_rank": 16,
        "packing": True,
    },
)
print(f"Job ID: {job.id}, Status: {job.status}")
```

`packing: True` is recommended for short customer support turns — it bin-packs multiple examples per context window for better GPU efficiency and gradient stability.

## Step 4: Monitor Training

```python
import time
while True:
    job = client.fine_tuning.jobs.retrieve(job.id)
    events = client.fine_tuning.jobs.list_events(job.id, limit=20).data
    for ev in reversed(events):
        print(f"[{ev.created_at}] {ev.message}")
    print(f"Status: {job.status}  Trained tokens: {job.trained_tokens}")
    if job.status in ("succeeded", "failed", "cancelled"):
        break
    time.sleep(30)
```

Status progression: `validating_files → queued → running → succeeded / failed`

## Step 5: Download Checkpoints (Optional)

```python
import os
checkpoints = client.fine_tuning.jobs.checkpoints.list(job.id).data
for ckpt in checkpoints:
    os.makedirs(ckpt.id, exist_ok=True)
    for file_id in ckpt.result_files:
        file_obj = client.files.retrieve(file_id)
        content = client.files.content(file_id)
        out_path = os.path.join(ckpt.id, os.path.basename(file_obj.filename))
        content.write_to_file(out_path)
```

## Key Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `n_epochs` | 3 | Good starting point for ~500 examples |
| `learning_rate_multiplier` | 2e-5 | Recommended default |
| `lora_rank` | 16 | Enables LoRA mode; omit for full fine-tuning |
| `packing` | true | Recommended for short samples |

## Next Steps

Once `status=succeeded`, use the `nebius-deploy-lora` skill to serve your adapter as a serverless endpoint on Token Factory.

Docs: https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune
