# Live Patching a Nebius Dedicated Endpoint to Increase max_replicas

## Overview

Nebius dedicated endpoints support **live patching** via a `PATCH` API call. You do not need to redeploy or recreate the endpoint to update scaling parameters like `max_replicas`.

## Using `curl`

```bash
curl -sS -X PATCH \
  "https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/ep-xyz789" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scaling": { "max_replicas": 8 }
  }'
```

## Using Python (`requests`)

```python
import os, json, requests

CONTROL_PLANE_BASE_URL = "https://api.tokenfactory.nebius.com"
API_TOKEN = os.environ["API_TOKEN"]
endpoint_id = "ep-xyz789"

payload = {
    "scaling": {"max_replicas": 8},
}

r = requests.patch(
    f"{CONTROL_PLANE_BASE_URL}/v0/dedicated_endpoints/{endpoint_id}",
    headers={"Authorization": f"Bearer {API_TOKEN}"},
    json=payload,
)
r.raise_for_status()
print(json.dumps(r.json(), indent=2))
```

## What Happens After the Patch?

- The control plane immediately acknowledges the new `max_replicas` of 8.
- The autoscaler provisions additional replicas (up to 8) as load requires.
- Billing applies when at least one replica is running.
- Monitor active replicas and traffic via **Navigation Bar → Inference → Observability**.
