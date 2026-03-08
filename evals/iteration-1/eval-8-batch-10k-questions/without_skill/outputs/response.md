# Running 10,000 Questions as a Batch Job on Nebius with Llama 70B

## Step 1: Prepare Your Input JSONL File

```python
import json

questions = [...]  # your 10,000 questions

with open("batch_input.jsonl", "w") as f:
    for i, question in enumerate(questions):
        record = {
            "custom_id": f"q-{i+1:05d}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a domain expert. Answer thoroughly."},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 1024
            }
        }
        f.write(json.dumps(record) + "\n")
```

## Step 2: Upload, Submit, Poll, Download

```python
import json, time
from openai import OpenAI

client = OpenAI(
    api_key="your_nebius_api_key_here",
    base_url="https://api.studio.nebius.com/v1/"
)

# Upload
with open("batch_input.jsonl", "rb") as f:
    uploaded_file = client.files.create(file=f, purpose="batch")

# Create batch
batch_job = client.batches.create(
    input_file_id=uploaded_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# Poll
while True:
    batch = client.batches.retrieve(batch_job.id)
    counts = batch.request_counts
    print(f"[{batch.status}] {counts.completed}/{counts.total} completed")
    if batch.status in ("completed", "failed", "cancelled", "expired"):
        break
    time.sleep(60)

# Download results
if batch.status == "completed":
    result = client.files.content(batch.output_file_id)
    with open("batch_output.jsonl", "wb") as f:
        f.write(result.content)
```

**Note:** Uses `api.studio.nebius.com` (old base URL) instead of `api.tokenfactory.nebius.com`. Uses `method: POST` field which is not in the Nebius docs format.
