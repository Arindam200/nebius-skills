# Deploying a HuggingFace-Hosted LoRA Adapter on Nebius Token Factory

## Overview

Nebius Token Factory supports deploying LoRA adapters directly from HuggingFace Hub without requiring you to upload local files.

## Step-by-Step: Deploy LoRA from HuggingFace

### Option 1: Via the Nebius AI Studio Console (UI)

1. Log in to [Nebius AI Studio](https://studio.nebius.ai/).
2. Navigate to **Token Factory** or **Fine-tuned Models** in the left sidebar.
3. Click **Deploy model** or **Create deployment**.
4. For the **Base model**, select **Llama 3.1 8B** from the catalog.
5. For the **Adapter / LoRA source**, choose **HuggingFace Hub** as the source type.
6. Enter the HuggingFace model identifier: `myorg/domain-lora`
7. If your HuggingFace repository is private, provide your **HuggingFace API token**.
8. Click **Deploy**.

### Option 2: Via the Nebius CLI

```bash
nebius ai model-deployment create \
  --base-model "meta-llama/Meta-Llama-3.1-8B-Instruct" \
  --adapter-source huggingface \
  --adapter-id "myorg/domain-lora" \
  --name "my-domain-lora-deployment" \
  --instance-type gpu.1xa100 \
  --replicas 1 \
  --hf-token "<YOUR_HF_TOKEN_IF_PRIVATE>"
```

### Option 3: Via the Nebius REST API

```bash
curl -X POST https://api.studio.nebius.ai/v1/deployments \
  -H "Authorization: Bearer <NEBIUS_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-domain-lora-deployment",
    "base_model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "adapter": {
      "source": "huggingface_hub",
      "model_id": "myorg/domain-lora"
    },
    "resources": {
      "instance_type": "gpu.1xa100",
      "replicas": 1
    }
  }'
```

**Note:** Uses `api.studio.nebius.ai` (old base URL). Does not use `/v0/models` endpoint. Guesses at the API structure rather than knowing it precisely.
