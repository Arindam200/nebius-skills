# Nebius Observability — Prometheus & Grafana Reference

> **When to read:** When the user asks about Prometheus scrape config, Grafana datasource setup, or alternative monitoring URLs.

Source: [Observability API integrations](https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations)

---

## Token Factory metrics endpoint (primary)

```
https://monitoring.tokenfactory.nebius.com/v1/projects/{PROJECT_ID}/prometheus/metrics
```

Use this for Token Factory inference workloads. All requests require `Authorization: Bearer {API_KEY}`.

---

## Alternative: Nebius Monitoring (federate)

For general Nebius cloud monitoring (not Token Factory–specific):

- **Prometheus federate URL:** `https://read.monitoring.api.nebius.cloud/projects/<project_ID>/service-provider/prometheus/federate`
- **Target:** `read.monitoring.api.nebius.cloud`

---

## Prometheus scrape config (Token Factory)

```yaml
scrape_configs:
  - job_name: nebius_token_factory
    metrics_path: /v1/projects/{PROJECT_ID}/prometheus/metrics
    scheme: https
    static_configs:
      - targets: ["monitoring.tokenfactory.nebius.com"]
    bearer_token: YOUR_API_KEY
    scrape_interval: 15s
```

Replace `{PROJECT_ID}` with your project ID from Project settings.

---

## Grafana datasource

- **Type:** Prometheus
- **URL:** `https://monitoring.tokenfactory.nebius.com` (or `https://read.monitoring.api.nebius.cloud` for federate)
- **Auth:** Add HTTP header `Authorization: Bearer YOUR_API_KEY`
- **Path:** For Token Factory, metrics are at `/v1/projects/{PROJECT_ID}/prometheus/...`

---

## Recommended scrape interval

Minimum: **15 seconds**. Shorter intervals may hit rate limits.
