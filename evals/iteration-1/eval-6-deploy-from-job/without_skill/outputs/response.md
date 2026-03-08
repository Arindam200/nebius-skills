# Deploying a Fine-Tuned Llama 3.1 8B as a Serverless LoRA Endpoint on Nebius

## Step 1: Retrieve Fine-Tuning Job Details

```python
import os
from nebius import SDK

sdk = SDK(credentials=os.environ["NEBIUS_API_KEY"])
job = sdk.fine_tuning.jobs.get("ftjob-xyz789")
print(job)
```

## Step 2: Deploy as a Serverless LoRA Endpoint

**Via Python SDK:**
```python
deployment = sdk.inference.deployments.create(
    model_id="meta-llama/Meta-Llama-3.1-8B-Instruct",
    lora_adapter_id="ftjob-xyz789",
    deployment_type="serverless",
    name="llama-3-1-8b-finetuned-lora",
)
print("Endpoint URL:", deployment.endpoint_url)
```

**Via CLI:**
```bash
nebius ai-studio deployment create \
  --model-id meta-llama/Meta-Llama-3.1-8B-Instruct \
  --lora-adapter-id ftjob-xyz789 \
  --type serverless \
  --name llama-3-1-8b-finetuned-lora
```

## Step 3: Wait for Active Status

```python
import time
while True:
    status = sdk.inference.deployments.get(deployment.id)
    if status.status == "ACTIVE":
        break
    time.sleep(15)
```

## Step 4: Query the Endpoint

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["NEBIUS_API_KEY"],
    base_url="https://api.studio.nebius.ai/v1",
)

response = client.chat.completions.create(
    model="llama-3-1-8b-finetuned-lora",
    messages=[{"role": "user", "content": "Your prompt here"}],
    max_tokens=512,
)
print(response.choices[0].message.content)
```

**Note:** Uses generic Nebius SDK patterns — actual API may differ. Uses `api.studio.nebius.ai` (old base URL) rather than `api.tokenfactory.nebius.com`.
