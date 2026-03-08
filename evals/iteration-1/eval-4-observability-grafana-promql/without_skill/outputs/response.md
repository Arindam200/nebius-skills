# Monitoring p95 Time-to-First-Token and Requests per Minute with Nebius Token Factory + Grafana

## Overview

Nebius Token Factory inference endpoints expose Prometheus-compatible metrics. Since you already use Grafana, the setup involves:
1. Configuring a Prometheus scrape job for your Token Factory endpoint
2. Adding Prometheus as a data source in Grafana
3. Building a dashboard with the relevant PromQL queries

## Step 1: Configure Prometheus Scrape Job

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'nebius_token_factory'
    static_configs:
      - targets:
          - '<token-factory-host>:<metrics-port>'
    metrics_path: /metrics
    scheme: http
    scrape_interval: 15s
```

## Step 2: Key Metrics (vLLM-based naming)

| Metric | Description |
|--------|-------------|
| `vllm:time_to_first_token_seconds_bucket` | TTFT histogram buckets |
| `vllm:time_to_first_token_seconds_count` | Total TTFT observations |
| `vllm:request_success_total` | Successful request counter |

## Step 3: PromQL Queries

**p95 Time-to-First-Token (5m window):**
```promql
histogram_quantile(
  0.95,
  sum(rate(vllm:time_to_first_token_seconds_bucket[5m])) by (le)
)
```

**Requests per Minute:**
```promql
sum(rate(vllm:time_to_first_token_seconds_count[1m])) * 60
```

## Step 4: Grafana Dashboard Panels

- Add a Time series panel for p95 TTFT, unit: `seconds`
- Add a Time series/Stat panel for RPM, unit: `requests/min`
- Optionally set alerts: e.g., alert if p95 TTFT > 2s

## Notes

- Exact metric names and endpoint URL should be verified in official Nebius documentation.
- Uses generic vLLM metric names — actual names may differ on Token Factory.
