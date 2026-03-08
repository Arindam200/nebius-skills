# Nebius Fine-Tuning — API Reference

> **When to read:** For hyperparameter details, API field specs, or when the user asks about job configuration, checkpoint structure, or dataset requirements.

Source: [Nebius Token Factory — How to fine-tune](https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune)

---

## Top-level job fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | yes | Base model to fine-tune (e.g. `meta-llama/Llama-3.1-8B-Instruct`) |
| `training_file` | string | yes | ID of file with `purpose="fine-tune"` |
| `validation_file` | string | no | Optional validation dataset |
| `suffix` | string | no | Human-readable suffix for the run (e.g. `customer-support-v1`) |
| `hyperparameters` | object | no | Fine-tuning config; omitted fields use defaults |
| `seed` | integer | no | Random seed for reproducibility |
| `integrations` | array | no | e.g. `wandb`, `hf` for metrics/export |

---

## Hyperparameters (common)

| Parameter | Default | Notes |
|-----------|---------|-------|
| `batch_size` | 8 | |
| `learning_rate` | 1e-5 | |
| `n_epochs` | 3 | Number of training passes |
| `warmup_ratio` | 0.0 | |
| `weight_decay` | 0.0 | |
| `lora` | true | Enable LoRA |
| `lora_r` | 16 | LoRA rank (maps to `lora_rank` in some APIs) |
| `lora_alpha` | 16 | |
| `lora_dropout` | 0.05 | |
| `packing` | true | Bin-pack short samples for efficiency |
| `max_grad_norm` | 1.0 | |
| `context_length` | 8192 | Max sequence length in tokens |

---

## Checkpoint download

Each checkpoint = model state after N training steps (often per epoch).

```python
checkpoints = client.fine_tuning.jobs.checkpoints.list(job.id).data
for checkpoint in checkpoints:
    for file_id in checkpoint.result_files:
        file_obj = client.files.retrieve(file_id)
        content = client.files.content(file_id)
        content.write_to_file(os.path.basename(file_obj.filename))
```

---

## Supported base models

Full list: https://docs.tokenfactory.nebius.com/post-training/models

Key deployable models:
- `meta-llama/Llama-3.1-8B-Instruct` — LoRA + full fine-tuning
- `meta-llama/Llama-3.3-70B-Instruct` — LoRA fine-tuning
