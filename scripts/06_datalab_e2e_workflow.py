"""
Nebius Token Factory — Full DataLab End-to-End Workflow
Docs: https://docs.tokenfactory.nebius.com/data-lab/overview
      https://docs.tokenfactory.nebius.com/data-lab/chat-completions
      https://docs.tokenfactory.nebius.com/data-lab/batch-inference
      https://docs.tokenfactory.nebius.com/data-lab/fine-tuning

This script orchestrates the complete DataLab pipeline:

  ┌─────────────────────────────────────────────────────────────┐
  │                    DataLab E2E Pipeline                     │
  │                                                             │
  │  [Seed Prompts]                                             │
  │       │                                                     │
  │       ▼                                                     │
  │  1. Generate inference logs (chat completions via API)      │
  │       │                                                     │
  │       ▼                                                     │
  │  2. Upload raw dataset to DataLab (JSONL)                   │
  │       │                                                     │
  │       ▼                                                     │
  │  3. Run Batch Inference → synthetic outputs dataset         │
  │       │                                                     │
  │       ▼                                                     │
  │  4. Download batch outputs, filter & reformat               │
  │       │                                                     │
  │       ▼                                                     │
  │  5. Upload curated dataset as fine-tuning training file     │
  │       │                                                     │
  │       ▼                                                     │
  │  6. Launch fine-tuning job                                  │
  │       │                                                     │
  │       ▼                                                     │
  │  7. Deploy fine-tuned LoRA adapter                          │
  │       │                                                     │
  │       ▼                                                     │
  │  8. Smoke-test the deployed model                           │
  └─────────────────────────────────────────────────────────────┘

Requirements: pip install openai requests
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY        = os.environ["NEBIUS_API_KEY"]
BASE_URL       = "https://api.tokenfactory.nebius.com/v1/"
CONTROL_URL    = "https://api.tokenfactory.nebius.com"
BASE_MODEL     = "meta-llama/Meta-Llama-3.1-8B-Instruct"
TEACHER_MODEL  = "meta-llama/Meta-Llama-3.1-70B-Instruct"  # larger model for data gen

LORA_RANK      = 16
N_EPOCHS       = 2

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ── Seed data for the domain we want to fine-tune on ─────────────────────────
DOMAIN_TOPICS = [
    "Explain vector databases and their use in RAG systems.",
    "What is the difference between embedding and re-ranking?",
    "How do you evaluate retrieval quality in a RAG pipeline?",
    "What are chunking strategies for document ingestion?",
    "Describe hybrid search combining dense and sparse retrieval.",
    "How does semantic caching work in LLM applications?",
    "What is a knowledge graph and how does it complement RAG?",
    "Explain the role of metadata filtering in vector search.",
    "What are the trade-offs between BM25 and dense retrieval?",
    "How do you handle long documents in a RAG architecture?",
]


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Generate inference logs (live chat completions as seed)
# ════════════════════════════════════════════════════════════════════════════
def step1_generate_inference_logs(topics: list[str]) -> list[dict]:
    print("\n[Step 1] Generating inference logs …")
    logs = []
    for topic in topics:
        resp = client.chat.completions.create(
            model=BASE_MODEL,
            messages=[{"role": "user", "content": topic}],
            max_tokens=256,
        )
        logs.append({
            "prompt":     topic,
            "completion": resp.choices[0].message.content,
            "model":      BASE_MODEL,
        })
        print(f"  ✓ {topic[:60]}")
    print(f"  Generated {len(logs)} log entries.")
    return logs


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Upload raw dataset to DataLab (via Files API as fine-tune file)
# ════════════════════════════════════════════════════════════════════════════
def step2_upload_raw_dataset(logs: list[dict], path: str = "raw_dataset.jsonl") -> str:
    print("\n[Step 2] Uploading raw dataset to DataLab …")
    with open(path, "w") as f:
        for entry in logs:
            record = {
                "messages": [
                    {"role": "user",      "content": entry["prompt"]},
                    {"role": "assistant", "content": entry["completion"] or ""},
                ]
            }
            f.write(json.dumps(record) + "\n")

    with open(path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="fine-tune")
    print(f"  Raw dataset file ID: {file_obj.id}")
    return file_obj.id


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Run Batch Inference (teacher model generates richer responses)
# ════════════════════════════════════════════════════════════════════════════
def step3_run_batch_inference(
    topics: list[str],
    batch_path: str = "batch_requests.jsonl",
) -> str:
    print("\n[Step 3] Running batch inference with teacher model …")

    # Build JSONL
    with open(batch_path, "w") as f:
        for topic in topics:
            req = {
                "custom_id": str(uuid.uuid4()),
                "url": "/v1/chat/completions",
                "body": {
                    "model": TEACHER_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert AI engineer. Provide detailed, "
                                "accurate answers suitable for training a smaller model."
                            ),
                        },
                        {"role": "user", "content": topic},
                    ],
                    "max_tokens":  1024,
                    "temperature": 0.6,
                },
            }
            f.write(json.dumps(req) + "\n")

    # Upload + create batch
    with open(batch_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="batch")

    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "datalab-e2e-teacher-distillation"},
    )
    print(f"  Batch job: {batch.id}  status={batch.status}")

    # Poll
    while True:
        time.sleep(30)
        batch = client.batches.retrieve(batch.id)
        counts    = batch.request_counts
        completed = counts.completed if counts else "?"
        total     = counts.total     if counts else "?"
        print(f"  status={batch.status}  completed={completed}/{total}")
        if batch.status in ("completed", "failed", "cancelled", "expired"):
            break

    return batch.id


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Download batch outputs, filter & reformat
# ════════════════════════════════════════════════════════════════════════════
def step4_download_and_curate(
    batch_id: str,
    id_map: dict[str, str],
    output_path: str = "curated_training.jsonl",
) -> str:
    print("\n[Step 4] Downloading batch outputs and curating dataset …")
    batch = client.batches.retrieve(batch_id)

    output_file_id = getattr(batch, "output_file_id", None)
    if not output_file_id:
        raise RuntimeError("Batch has no output file.")

    content = client.files.content(output_file_id)
    records = [json.loads(l) for l in content.text.strip().splitlines() if l.strip()]

    written = 0
    with open(output_path, "w") as f:
        for rec in records:
            cid    = rec.get("custom_id", "")
            choice = (rec.get("response", {}).get("body", {}).get("choices") or [{}])[0]
            reply  = choice.get("message", {}).get("content", "").strip()
            prompt = id_map.get(cid, "")

            # Quality filter: skip very short replies
            if not reply or len(reply) < 50:
                continue

            sample = {
                "messages": [
                    {"role": "user",      "content": prompt},
                    {"role": "assistant", "content": reply},
                ]
            }
            f.write(json.dumps(sample) + "\n")
            written += 1

    print(f"  Curated {written} high-quality examples → {output_path}")
    return output_path


def _load_id_map(batch_path: str) -> dict[str, str]:
    id_map: dict[str, str] = {}
    if Path(batch_path).exists():
        with open(batch_path) as f:
            for line in f:
                req = json.loads(line)
                user_msg = next(
                    (m["content"] for m in req["body"]["messages"] if m["role"] == "user"), ""
                )
                id_map[req["custom_id"]] = user_msg
    return id_map


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — Upload curated dataset as fine-tuning training file
# ════════════════════════════════════════════════════════════════════════════
def step5_upload_training_file(curated_path: str) -> str:
    print("\n[Step 5] Uploading curated dataset as fine-tuning training file …")
    with open(curated_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="fine-tune")
    print(f"  Training file ID: {file_obj.id}")
    return file_obj.id


# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Launch fine-tuning job
# ════════════════════════════════════════════════════════════════════════════
def step6_launch_finetuning(train_file_id: str) -> str:
    print("\n[Step 6] Launching fine-tuning job …")
    job = client.fine_tuning.jobs.create(
        model=BASE_MODEL,
        training_file=train_file_id,
        hyperparameters={  # type: ignore[arg-type]
            "n_epochs":                N_EPOCHS,
            "learning_rate_multiplier": 2e-5,
            "lora_rank":               LORA_RANK,
        },
    )
    print(f"  Job ID: {job.id}  status={job.status}")

    seen: set[str] = set()
    while True:
        time.sleep(30)
        job = client.fine_tuning.jobs.retrieve(job.id)
        for ev in reversed(client.fine_tuning.jobs.list_events(job.id, limit=20).data):
            if ev.id not in seen:
                print(f"    [{ev.created_at}] {ev.message}")
                seen.add(ev.id)
        print(f"  status={job.status}  trained_tokens={job.trained_tokens}")
        if job.status in ("succeeded", "failed", "cancelled"):
            break

    if job.status != "succeeded":
        raise RuntimeError(f"Fine-tuning failed: {getattr(job, 'error', '')}")

    # Get latest checkpoint
    checkpoints = client.fine_tuning.jobs.checkpoints.list(job.id).data
    latest = checkpoints[-1] if checkpoints else None
    if latest:
        print(f"  Latest checkpoint: {latest.id}  step={latest.step_number}")

    return job.id


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Deploy fine-tuned LoRA
# ════════════════════════════════════════════════════════════════════════════
def step7_deploy_lora(ft_job_id: str, adapter_name: str = "datalab-e2e-demo") -> dict:
    print("\n[Step 7] Deploying fine-tuned LoRA adapter …")

    # Get the last checkpoint
    checkpoints = client.fine_tuning.jobs.checkpoints.list(ft_job_id).data
    if not checkpoints:
        raise RuntimeError("No checkpoints found for job.")
    ckpt_id = checkpoints[-1].id

    payload = {
        "source":     f"{ft_job_id}:{ckpt_id}",
        "base_model": BASE_MODEL,
        "name":       adapter_name,
        "description": "DataLab E2E pipeline demo model",
    }
    r = requests.post(f"{CONTROL_URL}/v0/models", json=payload, headers=HEADERS)
    r.raise_for_status()
    model_info = r.json()
    model_name = model_info["name"]
    print(f"  Deploy initiated: {model_name}")

    # Wait for active
    for _ in range(60):
        time.sleep(10)
        r = requests.get(f"{CONTROL_URL}/v0/models/{model_name}", headers=HEADERS)
        r.raise_for_status()
        info = r.json()
        status = info.get("status", "?")
        print(f"  status={status}")
        if status == "active":
            print(f"  Model live: {info['name']}")
            return info
        if status == "error":
            raise RuntimeError(f"Deploy failed: {info.get('status_reason')}")

    raise TimeoutError("Model did not become active in time.")


# ════════════════════════════════════════════════════════════════════════════
# STEP 8 — Smoke-test the deployed model
# ════════════════════════════════════════════════════════════════════════════
def step8_smoke_test(model_full_name: str):
    print("\n[Step 8] Smoke-testing deployed model …")
    test_prompts = [
        "What is a vector database?",
        "Explain chunking strategies for RAG in one paragraph.",
    ]
    for prompt in test_prompts:
        resp = client.chat.completions.create(
            model=model_full_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        reply = resp.choices[0].message.content
        print(f"\n  Q: {prompt}")
        print(f"  A: {reply}")


# ════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════
def run_pipeline():
    print("=" * 65)
    print("  Nebius Token Factory — DataLab E2E Pipeline")
    print("=" * 65)

    # Step 1
    logs = step1_generate_inference_logs(DOMAIN_TOPICS)

    # Step 2 — upload raw logs so they are visible in DataLab
    step2_upload_raw_dataset(logs)

    # Step 3
    batch_id = step3_run_batch_inference(DOMAIN_TOPICS)

    # Step 4
    id_map       = _load_id_map("batch_requests.jsonl")
    curated_path = step4_download_and_curate(batch_id, id_map)

    # Step 5
    train_file_id = step5_upload_training_file(curated_path)

    # Step 6
    ft_job_id = step6_launch_finetuning(train_file_id)

    # Step 7
    model_info = step7_deploy_lora(ft_job_id)

    # Step 8
    step8_smoke_test(model_info["name"])

    print("\n" + "=" * 65)
    print("  Pipeline complete!")
    print(f"  Deployed model: {model_info['name']}")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline()
