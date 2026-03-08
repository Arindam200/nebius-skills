# Setting Up Prometheus to Scrape Nebius Token Factory Metrics

## Overview

Nebius Token Factory is a service in the Nebius AI Cloud platform. To scrape its metrics with Prometheus, you configure a scrape job with the correct endpoint URL and authentication.

## Metrics Endpoint

Nebius Token Factory typically exposes metrics at a path like:

```
https://iam.api.nebius.cloud/metrics
```

**Note:** The exact URL should be verified against the official Nebius documentation.

## Authentication

Nebius Cloud services use IAM tokens or API keys (Bearer tokens) for authentication. You will need a service account with read permissions, and its IAM token or API key.

## prometheus.yml Configuration

```yaml
global:
  scrape_interval: 60s
  evaluation_interval: 60s

scrape_configs:
  - job_name: 'nebius-token-factory'
    scheme: https
    metrics_path: /metrics
    static_configs:
      - targets:
          - 'iam.api.nebius.cloud'
    authorization:
      type: Bearer
      credentials_file: /etc/prometheus/nebius_iam_token
    tls_config:
      insecure_skip_verify: false
```

Store the IAM token in a file and refresh it periodically since tokens are short-lived (~12 hours):

```bash
nebius iam get-token > /etc/prometheus/nebius_iam_token
chmod 600 /etc/prometheus/nebius_iam_token
```

**Important:** The exact metrics endpoint, metric names, and required IAM roles should be verified in the official Nebius documentation at https://docs.nebius.com.
