"""
Nebius Token Factory — Dedicated Endpoints (Control Plane + Inference)
Docs: https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints

Control plane base: https://api.tokenfactory.nebius.com
Data plane (inference) per region:
  eu-north1  → https://api.tokenfactory.nebius.com
  eu-west1   → https://api.tokenfactory.eu-west1.nebius.com
  us-central1→ https://api.tokenfactory.us-central1.nebius.com

Operations:
  - list_templates()       browse available model templates
  - create_endpoint()      provision a new dedicated endpoint
  - get_endpoint()         inspect an existing endpoint
  - update_endpoint()      patch name / scaling live
  - run_inference()        chat-completions against the endpoint
  - delete_endpoint()      tear down
"""

import os
import json
import time
import requests
from openai import OpenAI

# ── Config ───────────────────────────────────────────────────────────────────
API_TOKEN         = os.environ["NEBIUS_API_KEY"]
CONTROL_BASE      = "https://api.tokenfactory.nebius.com"
INFERENCE_BASE    = "https://api.tokenfactory.nebius.com/v1/"   # eu-north1 default

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type":  "application/json",
}

openai_client = OpenAI(base_url=INFERENCE_BASE, api_key=API_TOKEN)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _get(path: str) -> dict:
    r = requests.get(f"{CONTROL_BASE}{path}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def _post(path: str, payload: dict) -> dict:
    r = requests.post(f"{CONTROL_BASE}{path}", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()


def _patch(path: str, payload: dict) -> dict:
    r = requests.patch(f"{CONTROL_BASE}{path}", headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()


def _delete(path: str) -> int:
    r = requests.delete(f"{CONTROL_BASE}{path}", headers=HEADERS)
    r.raise_for_status()
    return r.status_code


# ── Operations ───────────────────────────────────────────────────────────────
def list_templates() -> list[dict]:
    """Browse all deployable model templates."""
    data = _get("/v0/dedicated_endpoints/templates")
    templates = data.get("templates", data)
    for t in templates:
        print(f"  {t.get('template_name','?'):50s}  flavors={[f.get('flavor_name') for f in t.get('flavors',[])]}")
    return templates


def create_endpoint(
    template_name: str,
    flavor_name: str = "base",
    region: str = "eu-north1",
    min_replicas: int = 1,
    max_replicas: int = 2,
    display_name: str = "my-endpoint",
) -> dict:
    """Create a dedicated endpoint and wait until it is ready."""
    payload = {
        "name":       display_name,
        "template":   template_name,
        "flavor":     flavor_name,
        "region":     region,
        "scaling": {
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
        },
    }
    endpoint = _post("/v0/dedicated_endpoints", payload)
    endpoint_id = endpoint["endpoint_id"]
    print(f"Endpoint created: {endpoint_id}  status={endpoint.get('status','?')}")

    # Poll until ready
    while True:
        time.sleep(15)
        info = get_endpoint(endpoint_id)
        status = info.get("status", "unknown")
        print(f"  status={status}")
        if status == "ready":
            print(f"  routing_key={info.get('routing_key')}")
            return info
        if status in ("error", "failed"):
            raise RuntimeError(f"Endpoint failed: {info}")


def get_endpoint(endpoint_id: str) -> dict:
    return _get(f"/v0/dedicated_endpoints/{endpoint_id}")


def update_endpoint(endpoint_id: str, name: str | None = None,
                    min_replicas: int | None = None,
                    max_replicas: int | None = None) -> dict:
    payload: dict = {}
    if name:
        payload["name"] = name
    if min_replicas is not None or max_replicas is not None:
        payload["scaling"] = {}
        if min_replicas is not None:
            payload["scaling"]["min_replicas"] = min_replicas
        if max_replicas is not None:
            payload["scaling"]["max_replicas"] = max_replicas
    result = _patch(f"/v0/dedicated_endpoints/{endpoint_id}", payload)
    print(f"Updated endpoint {endpoint_id}: {json.dumps(result, indent=2)}")
    return result


def run_inference(routing_key: str, prompt: str) -> str:
    """Send a chat-completion request to the dedicated endpoint."""
    resp = openai_client.chat.completions.create(
        model=routing_key,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def delete_endpoint(endpoint_id: str):
    status = _delete(f"/v0/dedicated_endpoints/{endpoint_id}")
    print(f"Deleted endpoint {endpoint_id}  HTTP {status}")


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Available templates ===")
    templates = list_templates()

    # Pick first template for demo
    if not templates:
        raise SystemExit("No templates returned – check your API key / project.")

    tmpl = templates[0]["template_name"]
    print(f"\n=== Creating endpoint from template: {tmpl} ===")
    endpoint = create_endpoint(
        template_name=tmpl,
        display_name="demo-endpoint",
        min_replicas=1,
        max_replicas=2,
    )

    endpoint_id  = endpoint["endpoint_id"]
    routing_key  = endpoint["routing_key"]

    print(f"\n=== Running inference (routing_key={routing_key}) ===")
    reply = run_inference(routing_key or tmpl, "What is the capital of Finland?")
    print(f"Model reply: {reply}")

    print(f"\n=== Updating autoscaling ===")
    update_endpoint(endpoint_id, min_replicas=1, max_replicas=4)

    print(f"\n=== Tearing down endpoint ===")
    delete_endpoint(endpoint_id)
