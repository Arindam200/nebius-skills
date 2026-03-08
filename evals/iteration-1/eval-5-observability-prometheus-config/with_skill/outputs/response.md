# Setting Up Prometheus to Scrape Nebius Token Factory Metrics

Source: https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations

## Prerequisites

1. **Issue a static API key** in the Nebius Token Factory UI (Project settings → API keys).
2. **Get your Project ID**: Project settings → Copy project ID.

## Scrape URL

```
https://read.monitoring.api.nebius.cloud/projects/<project_ID>/service-provider/prometheus/federate
```

- Host: `read.monitoring.api.nebius.cloud`
- Scheme: `https`
- Path: `/projects/<project_ID>/service-provider/prometheus/federate`

## Authentication

Use a **Bearer token** — your static API key from the Nebius Token Factory UI.

## prometheus.yml Configuration

**Newer Prometheus versions** (with `metric_name_validation_scheme` and `scrape_protocols`):

```yaml
scrape_configs:
  - job_name: 'Export time series from Nebius Monitoring'
    honor_labels: true
    scrape_interval: 15s
    scheme: https
    metric_name_validation_scheme: legacy
    scrape_protocols:
      - OpenMetricsText0.0.1
    metrics_path: '/projects/<project_ID>/service-provider/prometheus/federate'
    params:
      match[]:
        - '{__name__=~".+"}'
    bearer_token: '<static_API_key>'
    static_configs:
      - targets:
        - 'read.monitoring.api.nebius.cloud'
```

**Older Prometheus versions**:

```yaml
scrape_configs:
  - job_name: 'Export time series from Nebius Monitoring'
    honor_labels: true
    scrape_interval: 15s
    scheme: https
    metrics_path: '/projects/<project_ID>/service-provider/prometheus/federate'
    params:
      match[]:
        - '{__name__=~".+"}'
    bearer_token: '<static_API_key>'
    static_configs:
      - targets:
        - 'read.monitoring.api.nebius.cloud'
```

## Key Parameters

| Parameter | What to set |
|---|---|
| `bearer_token` | Your static API key from Nebius Token Factory UI |
| `metrics_path` | Must include your project ID |
| `match[]` | `{__name__=~".+"}` collects all metrics |
| `scrape_interval` | Minimum recommended: **15 seconds** |

## Start Prometheus

```bash
./prometheus --config.file=prometheus.yml
```
