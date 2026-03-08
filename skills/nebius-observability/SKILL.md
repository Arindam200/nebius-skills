---
name: nebius-observability
description: Programmatic observability and metrics access for Nebius Token Factory inference. Use this skill whenever the user wants to query inference metrics, set up Prometheus scraping, connect Grafana, monitor latency or throughput, track error rates, or export LLM observability data from Token Factory. Trigger for phrases like "get Nebius metrics", "set up Prometheus for Token Factory", "monitor my Nebius inference", "check latency on my endpoint", "connect Grafana to Nebius", "export observability data", or any question about monitoring or metrics on Nebius.
---

# Nebius Inference Observability

Access real-time and historical metrics (latency, throughput, errors, scaling) for your Nebius Token Factory inference workloads via Prometheus-compatible API.

## Prerequisites

```bash
pip install requests pyyaml
export NEBIUS_API_KEY="your-static-api-key"    # create in UI: Project settings → API keys
export NEBIUS_PROJECT_ID="your-project-id"     # Project settings → Copy project ID
```

## Metrics endpoint

```
https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/metrics
```

All requests require `Authorization: Bearer {API_KEY}`.

## Available metrics

| Category | Key metrics |
|----------|-------------|
| **Traffic** | `nebius_requests_total`, `nebius_input_tokens_total`, `nebius_output_tokens_total` |
| **Latency** | `nebius_time_to_first_token_ms_bucket` (histogram), `nebius_e2e_latency_ms_bucket` |
| **Errors** | `nebius_errors_total` (by error code) |
| **Scaling** | `nebius_active_replicas` |
| **Token distribution** | `nebius_input_tokens_per_request_bucket`, `nebius_output_tokens_per_request_bucket` |

Filter dimensions: time range, model endpoint, project, API key, region, error code, prompt/latency range.

## Fetch raw metrics

```python
import requests, os

PROJECT_ID = os.environ["NEBIUS_PROJECT_ID"]
HEADERS = {"Authorization": f"Bearer {os.environ['NEBIUS_API_KEY']}"}

url = f"https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/metrics"
r = requests.get(url, headers=HEADERS)
print(r.text[:2000])   # Prometheus text format
```

## PromQL instant queries

```python
def promql(expr: str) -> list:
    url = f"https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/api/v1/query"
    r = requests.get(url, headers=HEADERS, params={"query": expr})
    return r.json()["data"]["result"]

# Examples
print(promql("rate(nebius_requests_total[5m]) * 60"))                              # req/min
print(promql("histogram_quantile(0.95, nebius_time_to_first_token_ms_bucket)"))    # p95 TTFT
print(promql("rate(nebius_errors_total[5m])"))                                     # error rate
print(promql("nebius_active_replicas"))                                            # replicas
```

## Set up Prometheus scraping

Generate `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s          # minimum recommended interval

scrape_configs:
  - job_name: nebius_token_factory
    metrics_path: /v1/projects/{PROJECT_ID}/prometheus/metrics
    scheme: https
    static_configs:
      - targets: ["monitoring.tokenfactory.nebius.com"]
    bearer_token: YOUR_API_KEY
```

Start: `./prometheus --config.file=prometheus.yml`

> Note: Prometheus is best for small infra. For large deployments, use Grafana directly.

## Connect Grafana

Add a Prometheus data source in Grafana:

```json
{
  "type": "prometheus",
  "url": "https://monitoring.tokenfactory.nebius.com",
  "httpHeaderName1": "Authorization",
  "httpHeaderValue1": "Bearer YOUR_API_KEY",
  "jsonData": {
    "httpMethod": "POST",
    "prometheusType": "Prometheus"
  }
}
```

Or: In Grafana UI → Connections → Add data source → Prometheus → set URL + Bearer token header.

## Data locality

Metrics are collected in the region where inference runs, but eventually consolidated in `eu-north1`. Use the **Region** filter to compare cross-region endpoints.

## Bundled reference

Read `references/prometheus-grafana.md` when the user asks about Prometheus scrape config, Grafana datasource setup, or alternative monitoring URLs.

## Reference script

Full working script with PromQL summary + prometheus.yml generator: `scripts/03_observability.py`

Docs: https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations
