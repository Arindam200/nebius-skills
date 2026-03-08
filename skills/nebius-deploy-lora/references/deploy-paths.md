# Nebius LoRA Deploy — Deployment Paths Reference

> **When to read:** When the user asks about deploying from HuggingFace, from a local archive, or about the exact `source` field format.

Source: [Deploy custom LoRA adapter model](https://docs.tokenfactory.nebius.com/post-training/deploy-custom-model)

---

## Path A — From Nebius fine-tuning job

Use after a fine-tuning job succeeds.

**Source format:** `{job_id}:{checkpoint_id}`

```python
# Get checkpoint ID
checkpoints = client.fine_tuning.jobs.checkpoints.list(job_id).data
checkpoint_id = checkpoints[-1].id  # or by step_number

# Deploy
payload = {
    "source": f"{job_id}:{checkpoint_id}",
    "base_model": "meta-llama/Llama-3.1-8B-Instruct",
    "name": "my-adapter-v1",
}
requests.post("https://api.tokenfactory.nebius.com/v0/models", json=payload, headers=headers)
```

---

## Path B — From HuggingFace

**Source format:** HuggingFace repo URL (no upload needed)

```python
payload = {
    "source": "https://huggingface.co/your-org/your-lora-adapter",
    "base_model": "meta-llama/Llama-3.1-8B-Instruct",
    "name": "hf-lora-demo",
}
```

---

## Path C — From local archive

1. Upload archive via `POST /v0/models/upload` (or `POST /v1/files/model_archive` in some docs)
2. Archive must contain `adapter_model.safetensors` and `adapter_config.json`
3. Max size: 500 MB

```python
# Upload
with open("adapter.tar.gz", "rb") as f:
    r = requests.post("https://api.tokenfactory.nebius.com/v1/files/model_archive",
                      headers={"Authorization": f"Bearer {api_key}"},
                      files={"file": ("adapter.tar.gz", f, "application/octet-stream")})
file_id = r.json()["id"]

# Deploy
payload = {"source": file_id, "base_model": "...", "name": "..."}
```

---

## Deployed model name format

`{base_model}-LoRa:{adapter_name}-{random_suffix}`

Example: `meta-llama/Llama-3.1-8B-Instruct-LoRa:my-adapter-v1-AbCd`

---

## Status lifecycle

`validating` → `active` (success) or `error` (failure; check `status_reason`)
