# Deploying a HuggingFace-hosted LoRA Adapter on Nebius Token Factory

You can deploy your adapter at `huggingface.co/myorg/domain-lora` directly without uploading any local file. Nebius Token Factory accepts a HuggingFace repository URL as the `source` field.

## Prerequisites

- `NEBIUS_API_KEY` set as an environment variable
- HuggingFace repo must contain `adapter_model.safetensors` and `adapter_config.json`
- Base model: `meta-llama/Meta-Llama-3.1-8B-Instruct`

## Python API (no upload needed)

```python
import requests
import os
from openai import OpenAI
import time

api_key = os.environ.get('NEBIUS_API_KEY')
api_url = "https://api.tokenfactory.nebius.com/"

client = OpenAI(base_url=api_url + "/v1", api_key=api_key)

def create_lora_from_file(name, source, base_model):
    response = requests.post(
        f"{api_url}/v0/models",
        json={
            "source": source,        # HuggingFace URL — no upload needed
            "base_model": base_model,
            "name": name,
            "description": "domain lora from HuggingFace"
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )
    return response.json()

def wait_for_validation(name, delay=5):
    while True:
        time.sleep(delay)
        lora_info = requests.get(
            f"{api_url}/v0/models/{name}",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        ).json()
        if lora_info.get("status") in {"active", "error"}:
            return lora_info

# Deploy directly from HuggingFace
lora_name = create_lora_from_file(
    "domain-lora",
    "https://huggingface.co/myorg/domain-lora",
    "meta-llama/Meta-Llama-3.1-8B-Instruct"
).get("name")

lora_info = wait_for_validation(lora_name)

if lora_info.get("status") == "active":
    print(f"Deployed as: {lora_name}")
    completion = client.chat.completions.create(
        model=lora_name,
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(completion.choices[0].message.content)
elif lora_info.get("status") == "error":
    print(f"Deployment failed: {lora_info['status_reason']}")
```

## What to expect

- Model enters `validating` status immediately
- On success: status changes to `active`
- On failure: status changes to `error` with details in `status_reason`
- Final model name: `meta-llama/Meta-Llama-3.1-8B-Instruct-LoRa:domain-lora-AbCd`

## Key points

- Pass the HuggingFace repo URL directly as `"source"` — no `upload_file` call needed
- Only `meta-llama/Meta-Llama-3.1-8B-Instruct` and `meta-llama/Llama-3.3-70B-Instruct` supported for serverless LoRA
- Repo must contain `adapter_model.safetensors` and `adapter_config.json`
