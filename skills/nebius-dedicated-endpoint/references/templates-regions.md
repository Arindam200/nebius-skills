# Nebius Dedicated Endpoints — Templates & Regions Reference

> **When to read:** When the user asks about available templates, GPU types, regions, or flavor differences.

Source: [Dedicated Endpoints](https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints)

---

## Key concepts

| Term | Description |
|------|--------------|
| **Template** | Deployable blueprint for a model. Defines supported `flavor_name`, `gpu_type`, regions. |
| **Flavor** | Template variant (e.g. `base`, `fast`) — different performance/cost. |
| **Endpoint** | Your dedicated deployment created from a template. |
| **endpoint_id** | Identifier for update/delete operations. |
| **routing_key** | Model identifier passed to inference calls. Returned at creation. |

---

## Create request body (required fields)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Display name |
| `model_name` | string | yes | Template model (e.g. `openai/gpt-oss-20b`) |
| `flavor_name` | string | yes | e.g. `base`, `fast` |
| `gpu_type` | string | yes | From template (e.g. `gpu-h100-sxm`) |
| `gpu_count` | integer | yes | GPUs per replica |
| `region` | string | yes | `eu-north1`, `eu-west1`, `us-central1` |
| `scaling.min_replicas` | integer | yes | Minimum replicas |
| `scaling.max_replicas` | integer | yes | Maximum replicas |

---

## Regions

| Region | Inference base URL |
|--------|--------------------|
| `eu-north1` | `https://api.tokenfactory.nebius.com/v1/` |
| `eu-west1` | `https://api.tokenfactory.eu-west1.nebius.com/v1/` |
| `us-central1` | `https://api.tokenfactory.us-central1.nebius.com/v1/` |

Use the region-specific URL for inference to avoid extra routing and reduce latency.

---

## List templates

```http
GET /v0/dedicated_endpoints/templates
```

Use the response as the source of truth for valid `model_name`, `flavor_name`, `gpu_type`, `region` combinations.

---

## PATCH updatable fields

- `name`, `description`, `enabled`
- `gpu_type`, `gpu_count`
- `scaling.min_replicas`, `scaling.max_replicas`

`region` cannot be updated after creation.
