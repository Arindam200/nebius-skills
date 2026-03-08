# Setting Up an Isolated GPT-OSS-20B Endpoint on Nebius (eu-west1, 2–5 Replicas)

## Prerequisites

```bash
pip install requests openai
export NEBIUS_API_KEY="your-key-here"
```

## Step 0 — Shared Setup

```python
import os, time, requests
from openai import OpenAI

API_KEY       = os.environ["NEBIUS_API_KEY"]
CONTROL_PLANE = "https://api.tokenfactory.nebius.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
}
```

## Step 1 — Verify the Template

```python
r = requests.get(
    f"{CONTROL_PLANE}/v0/dedicated_endpoints/templates",
    headers=HEADERS,
)
r.raise_for_status()

for t in r.json().get("templates", []):
    if "gpt-oss-20b" in t["template_name"].lower():
        print(t["template_name"], [f["flavor_name"] for f in t.get("flavors", [])])
# openai/gpt-oss-20b ['base', 'fast']
```

## Step 2 — Create the Endpoint

```python
payload = {
    "name":     "gpt-oss-20b-eu-west1",
    "template": "openai/gpt-oss-20b",
    "flavor":   "base",
    "region":   "eu-west1",
    "scaling":  {
        "min_replicas": 2,
        "max_replicas": 5,
    },
}

r = requests.post(
    f"{CONTROL_PLANE}/v0/dedicated_endpoints",
    headers=HEADERS,
    json=payload,
)
r.raise_for_status()

endpoint    = r.json()
endpoint_id = endpoint["endpoint_id"]
routing_key = endpoint["routing_key"]

print(f"Endpoint ID : {endpoint_id}")
print(f"Routing key : {routing_key}")
```

## Step 3 — Poll Until Ready

```python
def wait_for_ready(endpoint_id: str, poll_interval: int = 15) -> dict:
    while True:
        r = requests.get(
            f"{CONTROL_PLANE}/v0/dedicated_endpoints/{endpoint_id}",
            headers=HEADERS,
        )
        r.raise_for_status()
        data   = r.json()
        status = data.get("status", "unknown")
        print(f"status={status}")

        if status == "ready":
            return data
        if status in ("failed", "error"):
            raise RuntimeError(f"Endpoint failed: {status}")

        time.sleep(poll_interval)

endpoint_info = wait_for_ready(endpoint_id)
```

## Step 4 — Run a Test Inference

The data-plane URL for **eu-west1** is `https://api.tokenfactory.eu-west1.nebius.com/v1/`. Use the `routing_key` as the model name.

```python
client = OpenAI(
    base_url="https://api.tokenfactory.eu-west1.nebius.com/v1/",
    api_key=API_KEY,
)

response = client.chat.completions.create(
    model=routing_key,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": "What is the capital of France?"},
    ],
    max_tokens=128,
)

print(response.choices[0].message.content)
```

## Quick Reference

| Step | Method | Path | Key |
|------|--------|------|-----|
| List templates | GET | `/v0/dedicated_endpoints/templates` | `template_name` |
| Create | POST | `/v0/dedicated_endpoints` | `endpoint_id`, `routing_key` |
| Poll status | GET | `/v0/dedicated_endpoints/{id}` | `status == "ready"` |
| Inference | OpenAI client | `https://api.tokenfactory.eu-west1.nebius.com/v1/` | `model=routing_key` |
| Update scaling | PATCH | `/v0/dedicated_endpoints/{id}` | `scaling` |
| Delete | DELETE | `/v0/dedicated_endpoints/{id}` | — |
