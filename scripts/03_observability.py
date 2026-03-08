"""
Nebius Token Factory — Observability Programmatic Access
Docs: https://docs.tokenfactory.nebius.com/ai-models-inference/observability
      https://docs.tokenfactory.nebius.com/ai-models-inference/observability-api-integrations

Metrics are exposed via a Prometheus-compatible scrape endpoint.
This script:
  1. Generates a ready-to-use prometheus.yml for both old and new Prometheus versions
  2. Fetches raw metrics via HTTP (instant query using PromQL against the scrape URL)
  3. Prints a summary of key LLM inference metrics:
       - Requests per minute
       - Input / output tokens per minute
       - Latency percentiles
       - Error rates

Requirements:
  pip install requests prometheus-client pyyaml

Environment variables:
  NEBIUS_API_KEY   – static API key (create one in Token Factory UI → Project settings)
  NEBIUS_PROJECT_ID – your project ID (Project settings → Copy project ID)
"""

import os
import textwrap
import requests
import yaml  # type: ignore[import-untyped]

API_KEY    = os.environ["NEBIUS_API_KEY"]
PROJECT_ID = os.environ["NEBIUS_PROJECT_ID"]

METRICS_BASE = "https://monitoring.tokenfactory.nebius.com"
SCRAPE_PATH  = f"/v1/projects/{PROJECT_ID}/prometheus/metrics"
QUERY_PATH   = f"/v1/projects/{PROJECT_ID}/prometheus/api/v1/query"

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


# ── 1. Generate prometheus.yml ───────────────────────────────────────────────
def generate_prometheus_config(output_path: str = "prometheus.yml"):
    config = {
        "global": {
            "scrape_interval": "15s",
        },
        "scrape_configs": [
            {
                "job_name": "nebius_token_factory",
                "metrics_path": SCRAPE_PATH,
                "scheme": "https",
                "static_configs": [
                    {"targets": ["monitoring.tokenfactory.nebius.com"]}
                ],
                "bearer_token": API_KEY,
            }
        ],
    }
    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"prometheus.yml written to: {output_path}")
    print(f"\nStart Prometheus:\n  ./prometheus --config.file={output_path}\n")
    return output_path


# ── 2. Raw metric scrape ─────────────────────────────────────────────────────
def fetch_raw_metrics(limit_lines: int = 40) -> str:
    """Fetch raw Prometheus text-format metrics from the scrape endpoint."""
    url = f"{METRICS_BASE}{SCRAPE_PATH}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    lines = r.text.splitlines()
    sample = "\n".join(lines[:limit_lines])
    if len(lines) > limit_lines:
        sample += f"\n… ({len(lines) - limit_lines} more lines)"
    return sample


# ── 3. PromQL instant query ──────────────────────────────────────────────────
def promql_query(expr: str) -> list[dict]:
    """Execute an instant PromQL query and return result vector."""
    url = f"{METRICS_BASE}{QUERY_PATH}"
    r = requests.get(url, headers=HEADERS, params={"query": expr}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("result", [])


# ── 4. Human-readable metrics summary ───────────────────────────────────────
QUERIES = {
    "Requests/min (last 5m)":              "rate(nebius_requests_total[5m]) * 60",
    "Input tokens/min (last 5m)":          "rate(nebius_input_tokens_total[5m]) * 60",
    "Output tokens/min (last 5m)":         "rate(nebius_output_tokens_total[5m]) * 60",
    "p50 TTFT (ms)":                       "histogram_quantile(0.50, nebius_time_to_first_token_ms_bucket)",
    "p95 TTFT (ms)":                       "histogram_quantile(0.95, nebius_time_to_first_token_ms_bucket)",
    "p99 TTFT (ms)":                       "histogram_quantile(0.99, nebius_time_to_first_token_ms_bucket)",
    "Error rate (last 5m)":                "rate(nebius_errors_total[5m])",
    "Active replicas":                     "nebius_active_replicas",
}


def print_metrics_summary():
    print(f"\n{'Metric':<45} {'Value':>15}")
    print("-" * 62)
    for label, expr in QUERIES.items():
        try:
            results = promql_query(expr)
            if results:
                # Sum across all series (endpoints / models)
                total = sum(float(r["value"][1]) for r in results if r.get("value"))
                print(f"{label:<45} {total:>15.2f}")
            else:
                print(f"{label:<45} {'(no data)':>15}")
        except Exception as e:
            print(f"{label:<45} {'ERROR':>15}  ({e})")


# ── 5. Grafana datasource snippet ───────────────────────────────────────────
def print_grafana_snippet():
    snippet = textwrap.dedent(f"""
    # Add this as a Prometheus datasource in Grafana:
    #
    #   URL:            {METRICS_BASE}{SCRAPE_PATH}
    #   Authentication: Bearer token
    #   Token:          <your NEBIUS_API_KEY>
    #
    # Or use the JSON model:
    {{
      "type": "prometheus",
      "url": "{METRICS_BASE}",
      "httpHeaderName1": "Authorization",
      "httpHeaderValue1": "Bearer {API_KEY[:8]}…<redacted>",
      "jsonData": {{
        "httpMethod": "POST",
        "prometheusType": "Prometheus"
      }}
    }}
    """)
    print(snippet)


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Generating prometheus.yml ===")
    generate_prometheus_config()

    print("=== Live Metrics Summary ===")
    print_metrics_summary()

    print("\n=== Sample Raw Metrics (first 40 lines) ===")
    print(fetch_raw_metrics())

    print("\n=== Grafana Datasource Config ===")
    print_grafana_snippet()
