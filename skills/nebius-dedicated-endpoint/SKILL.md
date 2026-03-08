---
name: nebius-dedicated-endpoint
description: Create and manage dedicated inference endpoints on Nebius Token Factory. Use this skill whenever the user wants to deploy a model to a dedicated GPU instance, configure autoscaling, run inference against a private endpoint, update endpoint settings, or tear down a deployment. Trigger for phrases like "create a dedicated endpoint", "deploy a model on dedicated GPU", "set up autoscaling for my Nebius endpoint", "run inference on my dedicated model", "scale my endpoint", or any question about isolated/private inference deployments on Token Factory.
---

# Nebius Dedicated Endpoints

Dedicated endpoints give you an isolated, GPU-backed deployment of a supported model template with per-region data residency, configurable autoscaling, and OpenAI-compatible inference.

## Prerequisites

```bash
pip install requests openai
export NEBIUS_API_KEY="your-key"
```

**Control plane** (manage endpoints): `https://api.tokenfactory.nebius.com`
**Data plane** (inference), pick by region:

| Region | Inference base URL |
|--------|-------------------|
| eu-north1 | `https://api.tokenfactory.nebius.com/v1/` |
| eu-west1 | `https://api.tokenfactory.eu-west1.nebius.com/v1/` |
| us-central1 | `https://api.tokenfactory.us-central1.nebius.com/v1/` |

## Key concepts

- **Template** — deployable blueprint (model + supported GPU types/regions)
- **Flavor** — `base` (throughput-optimized) or `fast` (low-latency, speculative decoding)
- **Endpoint** — your live deployment, identified by `endpoint_id`
- **routing_key** — the model name to pass in inference calls

## Operations

### List available templates

```python
import requests
r = requests.get("https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/templates",
                 headers={"Authorization": f"Bearer {API_KEY}"})
templates = r.json().get("templates", [])
for t in templates:
    print(t["template_name"], [f["flavor_name"] for f in t.get("flavors", [])])
```

### Create an endpoint

```python
payload = {
    "name":     "my-endpoint",
    "template": "openai/gpt-oss-20b",      # from list_templates
    "flavor":   "base",
    "region":   "eu-north1",
    "scaling":  {"min_replicas": 1, "max_replicas": 2},
}
r = requests.post("https://api.tokenfactory.nebius.com/v0/dedicated_endpoints",
                  headers=HEADERS, json=payload)
endpoint = r.json()
endpoint_id  = endpoint["endpoint_id"]
routing_key  = endpoint["routing_key"]
```

Poll `GET /v0/dedicated_endpoints/{endpoint_id}` until `status == "ready"`.

### Run inference

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/", api_key=API_KEY)

resp = client.chat.completions.create(
    model=routing_key,          # the routing_key from endpoint creation
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

### Update autoscaling (live, no downtime)

```python
requests.patch(
    f"https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/{endpoint_id}",
    headers=HEADERS,
    json={"scaling": {"min_replicas": 2, "max_replicas": 8}},
)
```

### Delete endpoint

```python
requests.delete(
    f"https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/{endpoint_id}",
    headers=HEADERS,
)
```

## Choosing flavor

| Need | Use |
|------|-----|
| High throughput, cost-efficient | `base` |
| Low latency, real-time UX | `fast` (uses speculative decoding + smaller batches) |

## Data residency

Choose `region` to control where inference runs. Metrics are collected locally but stored in `eu-north1`.

## Bundled reference

Read `references/templates-regions.md` when the user asks about available templates, GPU types, regions, or flavor differences.

## Reference script

Full working script: `scripts/02_dedicated_endpoints.py`

Docs: https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints
