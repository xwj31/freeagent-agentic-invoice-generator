# FreeAgent agentic invoice generator

Lets an LLM (Claude Code) create clients and draft invoices in Hove Capital's FreeAgent account through the FreeAgent API.

Invoices are only ever created as drafts. `fa.py` refuses any request that would send an invoice or mark it as sent, so you check and send each invoice yourself in FreeAgent.

## Setup

Needs Python 3, no packages.

1. Create an app at https://dev.freeagent.com/apps/new with the redirect URI `http://localhost:8765/callback`.
2. Put the app's credentials in `.env` (gitignored):

   ```
   FREEAGENT_CLIENT_ID=...
   FREEAGENT_CLIENT_SECRET=...
   ```

   To use a sandbox account, also add `FREEAGENT_API=https://api.sandbox.freeagent.com/v2`.
3. Run `python3 get_token.py` and approve access in the browser. It saves `FREEAGENT_REFRESH_TOKEN` to `.env` and prints your company name to confirm the connection.

Run `get_token.py` again if the refresh token is ever revoked.

## Usage

`fa.py` calls any FreeAgent API endpoint and prints the JSON response. It gets a fresh access token on every call.

```sh
python3 fa.py GET /company
python3 fa.py GET '/contacts?view=all'
python3 fa.py POST /contacts '{"contact": {"organisation_name": "Acme Ltd", "email": "accounts@acme.com"}}'
python3 fa.py POST /invoices '{"invoice": {"contact": "https://api.freeagent.com/v2/contacts/123", "dated_on": "2026-09-29", "payment_terms_in_days": 30, "invoice_items": [{"item_type": "Hours", "quantity": "1.0", "price": "70.0", "sales_tax_rate": "20.0", "description": "Website work"}]}}'
```

API reference: https://dev.freeagent.com/docs

## Invoice rules

- Always charge 20% VAT on every item. Hove Capital is VAT registered.
- Use 30-day payment terms.
- Never send invoices from here. Send them from the FreeAgent UI.
