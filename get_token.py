"""Get a FreeAgent refresh token via http://localhost:8765/callback and save it to .env.

Needs FREEAGENT_CLIENT_ID and FREEAGENT_CLIENT_SECRET in .env.
Set FREEAGENT_API=https://api.sandbox.freeagent.com/v2 in .env to use the sandbox.
"""
import base64
import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV = Path(__file__).with_name(".env")
env = {
    k.strip(): v.strip().strip("\"'")
    for k, v in (line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line and not line.startswith("#"))
}
API = env.get("FREEAGENT_API", "https://api.freeagent.com/v2")
REDIRECT = "http://localhost:8765/callback"
STATE = secrets.token_urlsafe(16)
params = {}


def call(req):
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code} from {req.full_url}: {e.read().decode()}")


class Callback(BaseHTTPRequestHandler):
    def do_GET(self):
        params.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Done, you can close this tab.")

    def log_message(self, *args):
        pass


server = HTTPServer(("localhost", 8765), Callback)
url = f"{API}/approve_app?" + urllib.parse.urlencode(
    {"client_id": env["FREEAGENT_CLIENT_ID"], "response_type": "code", "redirect_uri": REDIRECT, "state": STATE}
)
print(f"Approve access in the browser:\n{url}")
webbrowser.open(url)
while "code" not in params and "error" not in params:
    server.handle_request()
if params.get("state") != [STATE] or "code" not in params:
    sys.exit(f"Bad callback: {params}")

basic = base64.b64encode(f"{env['FREEAGENT_CLIENT_ID']}:{env['FREEAGENT_CLIENT_SECRET']}".encode()).decode()
tokens = call(urllib.request.Request(
    f"{API}/token_endpoint",
    data=urllib.parse.urlencode({"grant_type": "authorization_code", "code": params["code"][0], "redirect_uri": REDIRECT}).encode(),
    headers={"Authorization": f"Basic {basic}"},
))

lines = [l for l in ENV.read_text().splitlines() if not l.startswith("FREEAGENT_REFRESH_TOKEN=")]
ENV.write_text("\n".join(lines + [f"FREEAGENT_REFRESH_TOKEN={tokens['refresh_token']}"]) + "\n")

company = call(urllib.request.Request(
    f"{API}/company", headers={"Authorization": f"Bearer {tokens['access_token']}", "Accept": "application/json"}
))["company"]
print(f"Connected to FreeAgent company: {company['name']}. Refresh token saved to .env.")
