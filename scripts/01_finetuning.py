"""
Nebius Token Factory — Fine-Tuning Workflow
Docs: https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune

Steps:
  1. Upload training (+ optional validation) JSONL datasets
  2. Create a fine-tuning job (LoRA or full)
  3. Poll status / stream events
  4. Download checkpoints when succeeded
"""

import os
import time
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY   = os.environ["NEBIUS_API_KEY"]
BASE_URL  = "https://api.tokenfactory.nebius.com/v1/"

TRAIN_FILE      = "training.jsonl"      # local path
VALID_FILE      = "validation.jsonl"    # optional – set to None to skip
BASE_MODEL      = "meta-llama/Meta-Llama-3.1-8B-Instruct"
N_EPOCHS        = 3
LEARNING_RATE   = 2e-5
LORA_RANK       = 16                    # set to None for full fine-tuning

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ── 1. Upload datasets ───────────────────────────────────────────────────────
def upload_dataset(path: str, label: str) -> str:
    print(f"Uploading {label} dataset: {path}")
    with open(path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="fine-tune")
    print(f"  → {label} file ID: {file_obj.id}")
    return file_obj.id


# ── 2. Create fine-tuning job ────────────────────────────────────────────────
def create_job(train_id: str, valid_id: str | None) -> str:
    hyperparams: dict = {
        "n_epochs": N_EPOCHS,
        "learning_rate_multiplier": LEARNING_RATE,
    }
    if LORA_RANK is not None:
        hyperparams["lora_rank"] = LORA_RANK

    job = client.fine_tuning.jobs.create(
        model=BASE_MODEL,
        training_file=train_id,
        **({"validation_file": valid_id} if valid_id else {}),  # type: ignore[arg-type]
        hyperparameters=hyperparams,  # type: ignore[arg-type]
    )
    print(f"Job created: {job.id}  status={job.status}")
    return job.id


# ── 3. Poll status + stream events ──────────────────────────────────────────
def wait_for_job(job_id: str, poll_interval: int = 30) -> object:
    seen_event_ids: set[str] = set()
    print(f"\nMonitoring job {job_id} …")

    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)

        # Print new events
        events = client.fine_tuning.jobs.list_events(job_id, limit=50).data
        for ev in reversed(events):
            if ev.id not in seen_event_ids:
                print(f"  [{ev.created_at}] {ev.message}")
                seen_event_ids.add(ev.id)

        print(f"  status={job.status}  trained_tokens={job.trained_tokens}")

        if job.status in ("succeeded", "failed", "cancelled"):
            if job.status == "failed":
                print(f"Job failed: {job.error}")
            return job

        time.sleep(poll_interval)


# ── 4. Download checkpoints ──────────────────────────────────────────────────
def download_checkpoints(job_id: str):
    checkpoints = client.fine_tuning.jobs.checkpoints.list(job_id).data
    if not checkpoints:
        print("No checkpoints found.")
        return

    for ckpt in checkpoints:
        out_dir = ckpt.id
        os.makedirs(out_dir, exist_ok=True)
        print(f"\nCheckpoint {ckpt.id}  step={ckpt.step_number}")

        for file_id in ckpt.result_files:  # type: ignore[attr-defined]
            file_obj  = client.files.retrieve(file_id)
            content   = client.files.content(file_id)
            out_path  = os.path.join(out_dir, os.path.basename(file_obj.filename))
            content.write_to_file(out_path)
            print(f"  Saved: {out_path}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    train_id = upload_dataset(TRAIN_FILE, "training")
    valid_id = upload_dataset(VALID_FILE, "validation") if VALID_FILE else None

    job_id  = create_job(train_id, valid_id)
    job     = wait_for_job(job_id)

    status = getattr(job, "status", "unknown")
    if status == "succeeded":
        download_checkpoints(job_id)
        print("\nFine-tuning complete. Checkpoints downloaded.")
    else:
        print(f"\nJob ended with status: {status}")
