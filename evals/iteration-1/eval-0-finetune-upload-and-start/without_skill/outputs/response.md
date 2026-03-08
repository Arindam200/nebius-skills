# Fine-Tuning Llama 3.1 8B on Nebius Token Factory with a Customer Support Dataset

## Prerequisites

- A Nebius AI account with access to Token Factory / Fine-tuning
- Your customer support dataset as a JSONL file (~500 examples)
- An API key from Nebius AI Studio

## Step 1: Prepare Your Dataset

Nebius Token Factory expects data in the OpenAI-compatible JSONL chat format. Each line must be a valid JSON object with a `messages` key.

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful customer support agent for Acme Corp."}, {"role": "user", "content": "How do I reset my password?"}, {"role": "assistant", "content": "To reset your password, click 'Forgot Password' on the login page and follow the instructions sent to your email."}]}
```

Split your 500 examples: ~450 for `train.jsonl` (90%) and ~50 for `val.jsonl` (10%).

## Step 2: Upload the Dataset Files

```bash
export NEBIUS_API_KEY="your_api_key_here"

# Upload training file
curl https://api.studio.nebius.ai/v1/files \
  -H "Authorization: Bearer $NEBIUS_API_KEY" \
  -F "purpose=fine-tune" \
  -F "file=@train.jsonl"

# Upload validation file
curl https://api.studio.nebius.ai/v1/files \
  -H "Authorization: Bearer $NEBIUS_API_KEY" \
  -F "purpose=fine-tune" \
  -F "file=@val.jsonl"
```

Save the returned `file_id` values from each response.

## Step 3: Create the LoRA Fine-Tuning Job

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_api_key_here",
    base_url="https://api.studio.nebius.ai/v1/",
)

job = client.fine_tuning.jobs.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    training_file="file-<your_train_file_id>",
    validation_file="file-<your_val_file_id>",
    method={
        "type": "supervised",
        "supervised": {
            "hyperparameters": {
                "n_epochs": 3,
                "learning_rate_multiplier": 2.0,
                "batch_size": 8,
            }
        },
    },
    suffix="customer-support-v1",
)
print("Job ID:", job.id)
```

## Step 4: Monitor and Use the Model

```python
# Monitor
job_status = client.fine_tuning.jobs.retrieve("<job_id>")
print(job_status.status)  # queued -> running -> succeeded

# Inference after success
completed_job = client.fine_tuning.jobs.retrieve("<job_id>")
response = client.chat.completions.create(
    model=completed_job.fine_tuned_model,
    messages=[{"role": "user", "content": "How do I track my order?"}],
)
print(response.choices[0].message.content)
```
