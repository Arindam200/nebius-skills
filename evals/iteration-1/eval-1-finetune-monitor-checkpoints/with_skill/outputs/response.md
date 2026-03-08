# Monitoring Fine-Tuning Job `ftjob-abc123` and Downloading Checkpoints

## Part 1: Stream Events While the Job is Running

The Nebius Token Factory API does not use a true SSE stream for fine-tuning. You "stream" events by polling `list_events` alongside `jobs.retrieve` in a loop:

```python
import os
import time
from openai import OpenAI

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=os.environ.get("NEBIUS_API_KEY"),
)

JOB_ID = "ftjob-abc123"
POLL_INTERVAL_SECONDS = 15
TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}

job = client.fine_tuning.jobs.retrieve(JOB_ID)
print(f"Starting status: {job.status}")

seen_event_ids = set()

while job.status not in TERMINAL_STATUSES:
    time.sleep(POLL_INTERVAL_SECONDS)
    job = client.fine_tuning.jobs.retrieve(JOB_ID)

    events = client.fine_tuning.jobs.list_events(JOB_ID)
    for event in reversed(events.data):  # oldest-first
        if event.id not in seen_event_ids:
            seen_event_ids.add(event.id)
            print(f"[{event.created_at}] [{event.level}] {event.message}")

    print(
        f"  Status: {job.status} | "
        f"Steps: {job.trained_steps}/{job.total_steps} | "
        f"Tokens trained: {job.trained_tokens}"
    )

print(f"\nFinal status: {job.status}")
if job.status == "failed":
    print(f"Error: {job.error}")
```

**Key job fields to watch:**

| Field | What it means |
|---|---|
| `status` | `validating_files` → `queued` → `running` → `succeeded`/`failed` |
| `trained_tokens` | Tokens processed so far |
| `trained_steps` / `total_steps` | Training loop progress |
| `error` | Structured error info when `status == "failed"` |

**cURL single fetch (wrap in a loop to poll):**
```bash
curl "https://api.tokenfactory.nebius.com/v1/fine_tuning/jobs/ftjob-abc123/events" \
  -H "Authorization: Bearer $NEBIUS_API_KEY"
```

## Part 2: Download Checkpoints After the Job Succeeds

Each checkpoint represents the model state after a set number of training steps. Once `job.status == "succeeded"`:

```python
if job.status == "succeeded":
    checkpoints = client.fine_tuning.jobs.checkpoints.list(JOB_ID).data

    for checkpoint in checkpoints:
        print(f"Checkpoint: {checkpoint.id}  step: {checkpoint.step_number}")
        os.makedirs(checkpoint.id, exist_ok=True)

        for file_id in checkpoint.result_files:
            file_obj = client.files.retrieve(file_id)
            filename = file_obj.filename

            file_content = client.files.content(file_id)
            output_path = os.path.join(checkpoint.id, os.path.basename(filename))
            file_content.write_to_file(output_path)
            print(f"  Saved: {output_path}")
```

**cURL equivalent:**
```bash
# Step 1: List checkpoints
curl "https://api.tokenfactory.nebius.com/v1/fine_tuning/jobs/ftjob-abc123/checkpoints" \
  -H "Authorization: Bearer $NEBIUS_API_KEY"

# Step 2: Download each file by ID
curl "https://api.tokenfactory.nebius.com/v1/files/<file_ID>/content" \
  -H "Authorization: Bearer $NEBIUS_API_KEY" \
  -o "<local_filename>"
```

**Key notes:**
- There is no native SSE stream; use a polling loop with a 15-second interval.
- The `list_events` call is paginated — track `seen_event_ids` to avoid printing duplicates.
- API base URL: `https://api.tokenfactory.nebius.com/v1`
