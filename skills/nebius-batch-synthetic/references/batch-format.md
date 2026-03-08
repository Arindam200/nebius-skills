# Nebius Batch Inference — Format & Limits Reference

> **When to read:** When the user asks about JSONL structure, file limits, or output format.

Source: [Batch inference](https://docs.tokenfactory.nebius.com/ai-models-inference/batch-inference)

---

## Cost & limits

| Constraint | Value |
|------------|-------|
| Cost vs real-time | **50% cheaper** |
| Rate limits | Not consumed |
| Max requests per file | 5,000,000 |
| Max file size | 10 GB |
| Completion window | 24 hours |
| Max batch files | 500 |

---

## JSONL input format

Each line = one request. All requests must use the same model.

```json
{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "openai/gpt-oss-120b", "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}], "max_tokens": 1000}}
```

| Field | Description |
|-------|-------------|
| `custom_id` | Unique ID to map results back to inputs |
| `url` | `/v1/chat/completions` or `/v1/embeddings` |
| `body.model` | Model ID — must be the same across the file |
| `body` | Standard chat completions / embeddings request body |

---

## Create batch

```python
client.batches.create(
    input_file_id=file_obj.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={"description": "synthetic-data-gen"},
)
```

---

## Output format

Each result line:

```json
{"id": "batch_req_123", "custom_id": "request-1", "response": {"choices": [{"message": {"content": "..."}}], ...}, "error": null}
```

Use `custom_id` to map outputs to inputs. Line order may differ from input.

Failed requests: use `error_file_id` from batch status to download error lines.
