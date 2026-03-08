# Monitoring a Nebius Fine-Tuning Job and Downloading Checkpoints

## Step 1: Stream Fine-Tuning Events

Nebius uses an OpenAI-compatible API. Use the `openai` Python SDK pointed at the Nebius base URL:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1/",
    api_key="YOUR_NEBIUS_API_KEY",
)

job_id = "ftjob-abc123"

for event in client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id):
    print(f"[{event.created_at}] {event.level}: {event.message}")
```

## Step 2: Poll Until Completion

```python
import time

while True:
    job = client.fine_tuning.jobs.retrieve(job_id)
    print(f"Status: {job.status}")
    if job.status in ("succeeded", "failed", "cancelled"):
        break
    time.sleep(30)
```

## Step 3: List Checkpoints

```python
checkpoints = client.fine_tuning.jobs.checkpoints.list(fine_tuning_job_id=job_id)
for ckpt in checkpoints:
    print(ckpt.id, ckpt.step_number, ckpt.fine_tuned_model_checkpoint)
```

## Step 4: Download Result Files

```python
for file_id in job.result_files:
    info = client.files.retrieve(file_id)
    content = client.files.retrieve_content(file_id)
    with open(info.filename, "wb") as f:
        f.write(content)
```

## Alternative: Nebius CLI

```bash
nebius ai fine-tuning job get --id ftjob-abc123
nebius ai fine-tuning job list-events --id ftjob-abc123
nebius ai fine-tuning job list-checkpoints --id ftjob-abc123
```

Key outputs after success: `job.fine_tuned_model` (model ID for inference) and `job.result_files` (downloadable artifacts).
