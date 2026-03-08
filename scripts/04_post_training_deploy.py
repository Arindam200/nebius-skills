"""
Nebius Token Factory — Post-Training: Deploy Fine-Tuned LoRA
Docs: https://docs.tokenfactory.nebius.com/post-training/deploy-custom-model
      https://docs.tokenfactory.nebius.com/post-training/overview

Two deployment paths:
  A) From a completed fine-tuning job + checkpoint  (create_lora_from_job)
  B) From a local archive / HuggingFace link         (create_lora_from_file)

After deployment the model is served as a serverless LoRA endpoint
with per-token billing via the standard OpenAI-compatible inference API.
"""

import os
import time
import requests
from openai import OpenAI
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY  = os.environ["NEBIUS_API_KEY"]
API_URL  = "https://api.tokenfactory.nebius.com"
V0_URL   = f"{API_URL}/v0/models"
V1_URL   = f"{API_URL}/v1/"

HEADERS = {
    "Content-Type":  "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

client = OpenAI(base_url=V1_URL, api_key=API_KEY)


# ── Path A: deploy from fine-tuning job + checkpoint ─────────────────────────
def create_lora_from_job(
    adapter_name: str,
    ft_job_id: str,
    ft_checkpoint_id: str,
    base_model: str,
    description: str = "",
) -> dict:
    """
    Deploy the LoRA adapter produced by a fine-tuning job.

    adapter_name       – e.g. "my-customer-support-v1"
    ft_job_id          – e.g. "ftjob-abc123"
    ft_checkpoint_id   – e.g. "ftckpt-xyz789"
    base_model         – e.g. "meta-llama/Meta-Llama-3.1-8B-Instruct"
    """
    source = f"{ft_job_id}:{ft_checkpoint_id}"
    payload = {
        "source":      source,
        "base_model":  base_model,
        "name":        adapter_name,
        "description": description,
    }
    r = requests.post(V0_URL, json=payload, headers=HEADERS)
    r.raise_for_status()
    result = r.json()
    print(f"[path A] Deploy initiated. name={result.get('name')}  status={result.get('status')}")
    return result


# ── Path B: deploy from local archive or HuggingFace link ────────────────────
def upload_lora_archive(archive_path: str) -> str:
    """Upload a local .tar.gz / .zip of adapter_model.safetensors + adapter_config.json."""
    upload_url = f"{API_URL}/v1/files/model_archive"
    with open(archive_path, "rb") as f:
        r = requests.post(
            upload_url,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": (Path(archive_path).name, f, "application/octet-stream")},
        )
    r.raise_for_status()
    file_id = r.json()["id"]
    print(f"[upload] Archive uploaded. file_id={file_id}")
    return file_id


def create_lora_from_file(
    adapter_name: str,
    base_model: str,
    archive_path: str | None = None,
    hf_link: str | None = None,
    description: str = "",
) -> dict:
    """
    Deploy a LoRA adapter from:
      - a local archive (.tar.gz containing adapter_model.safetensors + adapter_config.json)
      - OR a Hugging Face repository URL
    """
    if not archive_path and not hf_link:
        raise ValueError("Provide either archive_path or hf_link")

    if archive_path:
        source = upload_lora_archive(archive_path)
    else:
        source = hf_link  # type: ignore[assignment]

    payload = {
        "source":      source,
        "base_model":  base_model,
        "name":        adapter_name,
        "description": description,
    }
    r = requests.post(V0_URL, json=payload, headers=HEADERS)
    r.raise_for_status()
    result = r.json()
    print(f"[path B] Deploy initiated. name={result.get('name')}  status={result.get('status')}")
    return result


# ── Wait for validation ──────────────────────────────────────────────────────
def wait_for_validation(model_name: str, poll_interval: int = 10, timeout: int = 600) -> dict:
    """Poll until model status is 'active' or 'error'."""
    deadline = time.time() + timeout
    print(f"Waiting for model '{model_name}' to become active …")
    while time.time() < deadline:
        time.sleep(poll_interval)
        r = requests.get(f"{V0_URL}/{model_name}", headers=HEADERS)
        r.raise_for_status()
        info = r.json()
        status = info.get("status", "unknown")
        print(f"  status={status}")
        if status == "active":
            print(f"  Model is live: {info.get('name')}")
            return info
        if status == "error":
            raise RuntimeError(f"Validation failed: {info.get('status_reason')}")
    raise TimeoutError(f"Model did not become active within {timeout}s")


# ── Inference with deployed LoRA ─────────────────────────────────────────────
def chat(model_full_name: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model_full_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


# ── List custom models ───────────────────────────────────────────────────────
def list_custom_models() -> list[dict]:
    r = requests.get(V0_URL, headers=HEADERS)
    r.raise_for_status()
    models = r.json().get("data", [])
    for m in models:
        print(f"  {m.get('name','?'):70s}  status={m.get('status','?')}")
    return models


# ── Delete deployed model ────────────────────────────────────────────────────
def delete_model(model_full_name: str):
    r = requests.delete(f"{V0_URL}/{model_full_name}", headers=HEADERS)
    r.raise_for_status()
    print(f"Deleted model: {model_full_name}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Listing existing custom models ===")
    list_custom_models()

    # --- Example: deploy from a completed fine-tuning job ---
    # Uncomment and fill in real IDs to run:
    #
    # result = create_lora_from_job(
    #     adapter_name      = "my-lora-v1",
    #     ft_job_id         = "ftjob-abc123",
    #     ft_checkpoint_id  = "ftckpt-xyz789",
    #     base_model        = "meta-llama/Meta-Llama-3.1-8B-Instruct",
    # )
    # model_name = result["name"]
    # info = wait_for_validation(model_name)
    # reply = chat(info["name"], "Hello, how can you help me today?")
    # print(f"Model says: {reply}")
    # delete_model(info["name"])

    # --- Example: deploy from HuggingFace link ---
    # result = create_lora_from_file(
    #     adapter_name = "hf-lora-demo",
    #     base_model   = "meta-llama/Meta-Llama-3.1-8B-Instruct",
    #     hf_link      = "https://huggingface.co/your-org/your-lora-adapter",
    # )

    print("\nDone. Uncomment the example blocks above to deploy a real model.")
