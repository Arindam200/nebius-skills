"""
Nebius Token Factory — Batch Inference for Synthetic Data Generation
Docs: https://docs.tokenfactory.nebius.com/ai-models-inference/batch-inference

Use-case: generate a large synthetic dataset (e.g. instruction-response pairs,
QA pairs, chain-of-thought examples) at 50% cost vs real-time inference,
asynchronously, with no rate-limit impact.

Pipeline:
  1. Build a JSONL batch file from a list of prompts / seed data
  2. Upload the batch file
  3. Create a batch job
  4. Poll until complete
  5. Download and parse outputs
  6. Optionally write outputs as a fine-tuning-ready conversational JSONL

Limits:  up to 5,000,000 requests • 10 GB file • completed within 24 h
Cost:    50% cheaper than real-time  • doesn't count against rate limits
"""

import json
import os
import time
import uuid
from pathlib import Path
from openai import OpenAI

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY  = os.environ["NEBIUS_API_KEY"]
BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODEL    = "meta-llama/Meta-Llama-3.1-70B-Instruct"   # any supported model ID

SYSTEM_PROMPT = (
    "You are a helpful assistant that generates high-quality training examples. "
    "Answer concisely and accurately."
)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ── 1. Build JSONL batch file from seed topics ───────────────────────────────
def build_batch_file(
    topics: list[str],
    output_path: str = "batch_requests.jsonl",
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    For each topic, create a chat-completion request line.
    Returns path to the written JSONL file.
    """
    with open(output_path, "w") as f:
        for topic in topics:
            request = {
                "custom_id": str(uuid.uuid4()),
                "url": "/v1/chat/completions",
                "body": {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": topic},
                    ],
                    "max_tokens":  max_tokens,
                    "temperature": temperature,
                },
            }
            f.write(json.dumps(request) + "\n")

    n = len(topics)
    print(f"Batch file written: {output_path}  ({n} requests)")
    return output_path


# ── 2. Upload batch file ─────────────────────────────────────────────────────
def upload_batch_file(path: str) -> str:
    with open(path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="batch")
    print(f"Uploaded batch file: {file_obj.id}")
    return file_obj.id


# ── 3. Create batch job ──────────────────────────────────────────────────────
def create_batch(file_id: str, description: str = "synthetic-data-gen") -> str:
    batch = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": description},
    )
    print(f"Batch created: {batch.id}  status={batch.status}")
    return batch.id


# ── 4. Poll until complete ───────────────────────────────────────────────────
def wait_for_batch(batch_id: str, poll_interval: int = 30) -> object:
    print(f"\nMonitoring batch {batch_id} …")
    while True:
        batch = client.batches.retrieve(batch_id)
        counts = batch.request_counts
        completed = counts.completed if counts else "?"
        failed    = counts.failed    if counts else "?"
        total     = counts.total     if counts else "?"
        print(f"  status={batch.status}  completed={completed}  failed={failed}  total={total}")
        if batch.status in ("completed", "failed", "cancelled", "expired"):
            return batch
        time.sleep(poll_interval)


# ── 5. Download and parse outputs ────────────────────────────────────────────
def download_outputs(batch: object) -> list[dict]:
    output_file_id = getattr(batch, "output_file_id", None)
    if not output_file_id:
        print("No output file available.")
        return []

    content = client.files.content(output_file_id)
    lines   = content.text.strip().splitlines()
    results = [json.loads(line) for line in lines if line.strip()]
    print(f"Downloaded {len(results)} output records.")
    return results


# ── 6. Convert to fine-tuning conversational JSONL ──────────────────────────
def export_as_training_data(
    results: list[dict],
    output_path: str = "synthetic_training.jsonl",
) -> str:
    """
    Write a conversational JSONL ready for fine-tuning upload.
    Maps custom_id → original user prompt via a lookup dict.
    """
    # Build lookup: custom_id → original user message
    id_to_prompt: dict[str, str] = {}
    batch_file   = "batch_requests.jsonl"
    if Path(batch_file).exists():
        with open(batch_file) as f:
            for line in f:
                req = json.loads(line)
                user_msg = next(
                    (m["content"] for m in req["body"]["messages"] if m["role"] == "user"), ""
                )
                id_to_prompt[req["custom_id"]] = user_msg

    written = 0
    with open(output_path, "w") as f:
        for rec in results:
            cid    = rec.get("custom_id", "")
            body   = rec.get("response", {}).get("body", {})
            choice = (body.get("choices") or [{}])[0]
            reply  = choice.get("message", {}).get("content", "").strip()
            if not reply:
                continue

            prompt = id_to_prompt.get(cid, "")
            sample = {
                "messages": [
                    {"role": "system",    "content": SYSTEM_PROMPT},
                    {"role": "user",      "content": prompt},
                    {"role": "assistant", "content": reply},
                ]
            }
            f.write(json.dumps(sample) + "\n")
            written += 1

    print(f"Training JSONL written: {output_path}  ({written} examples)")
    return output_path


# ── Seed topics (replace with your own) ─────────────────────────────────────
SEED_TOPICS = [
    "Explain the difference between supervised and unsupervised learning.",
    "What is gradient descent and why is it used in machine learning?",
    "Describe how transformer attention mechanisms work.",
    "What are the key differences between LoRA and full fine-tuning?",
    "How does speculative decoding speed up LLM inference?",
    "What is KV cache and how does it help with inference performance?",
    "Explain the concept of perplexity in language models.",
    "What is RLHF and how is it used to align language models?",
    "Describe the role of tokenization in NLP pipelines.",
    "What are the trade-offs between model size and inference latency?",
]


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Step 1: Build batch request file ===")
    batch_path = build_batch_file(SEED_TOPICS)

    print("\n=== Step 2: Upload batch file ===")
    file_id = upload_batch_file(batch_path)

    print("\n=== Step 3: Create batch job ===")
    batch_id = create_batch(file_id, description="ml-concepts-synthetic-data")

    print("\n=== Step 4: Wait for completion ===")
    batch = wait_for_batch(batch_id)

    status = getattr(batch, "status", "unknown")
    if status == "completed":
        print("\n=== Step 5: Download outputs ===")
        results = download_outputs(batch)

        print("\n=== Step 6: Export as training data ===")
        export_as_training_data(results)
        print("\nSynthetic dataset ready for fine-tuning!")
    else:
        print(f"\nBatch ended with status: {status}")
        error_file = getattr(batch, "error_file_id", None)
        if error_file:
            errors = client.files.content(error_file)
            print("Errors:\n", errors.text[:2000])
