# Live Patch: Increase max_replicas on Nebius Dedicated Endpoint ep-xyz789

## Overview

Nebius dedicated endpoints support **live autoscaling updates** with zero downtime and no redeployment. Use a `PATCH` request to the control-plane API.

## The PATCH Request

```python
import requests

API_KEY = "your-key"
endpoint_id = "ep-xyz789"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

response = requests.patch(
    f"https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/{endpoint_id}",
    headers=HEADERS,
    json={"scaling": {"min_replicas": 1, "max_replicas": 8}},
)

print(response.status_code)
print(response.json())
```

## Or with curl

```bash
curl -sS -X PATCH \
  "https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/ep-xyz789" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scaling": {"max_replicas": 8}}'
```

## Verify the Update

```python
r = requests.get(
    f"https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/{endpoint_id}",
    headers=HEADERS,
)
endpoint = r.json()
print(endpoint["scaling"])  # expect max_replicas: 8
print(endpoint["status"])   # expect "ready"
```

## Key Details

| Field | Value |
|---|---|
| Method | `PATCH` |
| URL | `https://api.tokenfactory.nebius.com/v0/dedicated_endpoints/ep-xyz789` |
| Payload | `{"scaling": {"max_replicas": 8}}` |
| Downtime | **None** |
| Redeployment | **Not required** |

- The new `max_replicas` takes effect immediately — the autoscaler will spin up additional replicas as demand rises.
- The `routing_key` and inference URL remain unchanged.
- The control-plane URL is always `https://api.tokenfactory.nebius.com` regardless of region.
