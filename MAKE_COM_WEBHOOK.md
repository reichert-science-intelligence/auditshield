# Make.com Webhook — Trial Key Email (Phase 8)

## Overview
When `WEBHOOK_URL` is set, `capture_lead(..., auto_provision_trial=True)` fires a POST to that URL with:
```json
{
  "event": "trial_provisioned",
  "email": "user@example.com",
  "trial_key": "pro-TRIAL-xxxxxxxx",
  "trial_expires": "2025-03-15T...",
  "source": "web"
}
```

## Make.com Scenario Wiring

1. **Webhooks** → **Custom webhook** — Create webhook, copy URL.
2. **Env:** Set `WEBHOOK_URL` to that URL (e.g. `https://hook.eu1.make.com/xxxxx`).
3. **Scenario:** Webhook trigger → **HTTP** → Gmail/SendGrid "Send Email".
4. **Email template:** Use `{{email}}` for To, include `{{trial_key}}` in body.
5. **Test:** Submit trial form → webhook fires → email sent.

## Local Testing
```bash
# Use a request bin to capture payload
export WEBHOOK_URL="https://webhook.site/your-unique-id"
# Run app, submit form, inspect POST at webhook.site
```
