---
name: nebius-deploy-lora
description: Deploy a fine-tuned LoRA adapter as a serverless endpoint on Nebius Token Factory. Use this skill whenever the user wants to serve a fine-tuned model, deploy a LoRA adapter from a Nebius fine-tuning job or HuggingFace, check deployment status, or delete a deployed custom model. Trigger for phrases like "deploy my fine-tuned model", "serve my LoRA adapter on Nebius", "deploy from fine-tuning checkpoint", "upload LoRA to Nebius", "deploy from HuggingFace", "delete my custom model", or any question about making a trained model available for inference on Token Factory.
---

# Nebius Post-Training: Deploy LoRA Adapter

Serve your fine-tuned LoRA adapter as a serverless endpoint with per-token billing. Two deployment paths: from a Nebius fine-tuning job, or from a local archive / HuggingFace link.

## Prerequisites

```bash
pip install requests openai
export NEBIUS_API_KEY="your-key"
```

API: `https://api.tokenfactory.nebius.com`

## Supported base models for serverless LoRA deployment

| Base model | Fine-tuning type |
|------------|-----------------|
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | LoRA + full (LoRA deployable) |
| `meta-llama/Llama-3.3-70B-Instruct` | LoRA (deployable) |

Full list: https://docs.tokenfactory.nebius.com/post-training/models

## Path A — Deploy from Nebius fine-tuning job

Use after a fine-tuning job succeeds (see **nebius-finetune** skill for the job step).

```python
import requests, os

api_key = os.environ["NEBIUS_API_KEY"]
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

# Get checkpoint ID first
from openai import OpenAI
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=api_key)
checkpoints = client.fine_tuning.jobs.checkpoints.list("ftjob-abc123").data
ckpt_id = checkpoints[-1].id   # use latest checkpoint

# Deploy
payload = {
    "source":      f"ftjob-abc123:{ckpt_id}",
    "base_model":  "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "name":        "my-adapter-v1",
    "description": "Customer support model v1",
}
r = requests.post("https://api.tokenfactory.nebius.com/v0/models", json=payload, headers=headers)
model_name = r.json()["name"]
```

## Path B — Deploy from HuggingFace or local archive

**HuggingFace link** (no upload needed):
```python
payload = {
    "source":     "https://huggingface.co/your-org/your-lora-adapter",
    "base_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "name":       "hf-lora-demo",
}
```

**Local archive** (must contain `adapter_model.safetensors` + `adapter_config.json`, max 500 MB):
```python
# First upload the archive
with open("adapter.tar.gz", "rb") as f:
    r = requests.post("https://api.tokenfactory.nebius.com/v1/files/model_archive",
                      headers={"Authorization": f"Bearer {api_key}"},
                      files={"file": ("adapter.tar.gz", f, "application/octet-stream")})
file_id = r.json()["id"]

# Then deploy using the file_id as source
payload = {"source": file_id, "base_model": "...", "name": "..."}
```

## Wait for validation

```python
import time

while True:
    time.sleep(10)
    r = requests.get(f"https://api.tokenfactory.nebius.com/v0/models/{model_name}", headers=headers)
    info = r.json()
    print(f"status={info['status']}")
    if info["status"] == "active":
        print(f"Live model name: {info['name']}")
        break
    if info["status"] == "error":
        raise RuntimeError(info.get("status_reason"))
```

## Deployed model name format

`{base_model}-LoRa:{adapter_name}-{random_suffix}`

Example: `meta-llama/Meta-Llama-3.1-8B-Instruct-LoRa:my-adapter-v1-AbCd`

## Run inference

```python
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=api_key)
resp = client.chat.completions.create(
    model=info["name"],    # full deployed model name
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

## List all custom models

```python
r = requests.get("https://api.tokenfactory.nebius.com/v0/models", headers=headers)
for m in r.json().get("data", []):
    print(f"{m['name']}  status={m['status']}")
```

## Delete model

```python
requests.delete(f"https://api.tokenfactory.nebius.com/v0/models/{model_name}", headers=headers)
```

## Reference script

Full working script: `scripts/04_post_training_deploy.py`

Docs: https://docs.tokenfactory.nebius.com/post-training/deploy-custom-model
