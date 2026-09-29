"""Call the FreeAgent API with the credentials in .env.

Usage: python3 fa.py GET /contacts
       python3 fa.py POST /invoices '{"invoice": {...}}'
Sending invoices is blocked on purpose, send them from the FreeAgent UI.
"""
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV = Path(__file__).with_name(".env")
env = {
    k.strip(): v.strip().strip("\"'")
    for k, v in (line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line and not line.startswith("#"))
}
API = env.get("FREEAGENT_API", "https://api.freeagent.com/v2")
BLOCKED = ("send_email", "mark_as_sent", "mark_as_scheduled")


def request(method, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code} from {method} {url}: {e.read().decode()}")


def access_token():
    basic = base64.b64encode(f"{env['FREEAGENT_CLIENT_ID']}:{env['FREEAGENT_CLIENT_SECRET']}".encode()).decode()
    tokens = request("POST", f"{API}/token_endpoint", urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": env["FREEAGENT_REFRESH_TOKEN"]}
    ).encode(), {"Authorization": f"Basic {basic}"})
    # Keep .env working if FreeAgent ever rotates the refresh token.
    if tokens.get("refresh_token", env["FREEAGENT_REFRESH_TOKEN"]) != env["FREEAGENT_REFRESH_TOKEN"]:
        lines = [l for l in ENV.read_text().splitlines() if not l.startswith("FREEAGENT_REFRESH_TOKEN=")]
        ENV.write_text("\n".join(lines + [f"FREEAGENT_REFRESH_TOKEN={tokens['refresh_token']}"]) + "\n")
    return tokens["access_token"]


def api(method, path, body=None):
    if any(b in path for b in BLOCKED):
        sys.exit(f"Blocked: {path} would send or mark an invoice as sent.")
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    return request(method, url, data, {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"})


if __name__ == "__main__":
    method, path, *body = sys.argv[1:]
    print(json.dumps(api(method.upper(), path, json.loads(body[0]) if body else None), indent=2))
