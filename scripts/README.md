# Nebius Token Factory — Scripts

Scripts built from the Nebius Token Factory docs.
API base: `https://api.tokenfactory.nebius.com`

## Setup

```bash
pip install -r requirements.txt
export NEBIUS_API_KEY="your-key-here"
export NEBIUS_PROJECT_ID="your-project-id"   # needed for observability only
```

## Scripts

| File | What it does |
|------|-------------|
| `01_finetuning.py` | Upload datasets → create LoRA fine-tuning job → poll events → download checkpoints |
| `02_dedicated_endpoints.py` | List templates → create dedicated endpoint → run inference → update autoscaling → delete |
| `03_observability.py` | Generate `prometheus.yml` · fetch raw metrics · PromQL instant queries · Grafana config |
| `04_post_training_deploy.py` | Deploy fine-tuned LoRA (from job/checkpoint or HuggingFace) → wait for validation → inference → delete |
| `05_batch_inference_synthetic.py` | Build JSONL → upload → create batch job → poll → download → export as training data |
| `06_datalab_e2e_workflow.py` | Full pipeline: inference logs → batch inference (teacher distillation) → curate → fine-tune → deploy → smoke test |

## Key Concepts

- **Fine-tuning**: `POST /v1/fine_tuning/jobs` — LoRA (`lora_rank`) or full weights
- **Dedicated endpoints**: `POST /v0/dedicated_endpoints` — isolated GPU deployments, per-region
- **Observability**: Prometheus scrape at `/v1/projects/{project_id}/prometheus/metrics`
- **Batch inference**: `POST /v1/batches` — 50% cheaper, async, up to 5M requests / 10 GB
- **Custom model deploy**: `POST /v0/models` — LoRA adapter served serverlessly

## Docs
- https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune
- https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints
- https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations
- https://docs.tokenfactory.nebius.com/ai-models-inference/batch-inference
- https://docs.tokenfactory.nebius.com/data-lab/overview
