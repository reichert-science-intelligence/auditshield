# RSI ACADEMY — Stripe SKU Scaffold (S30)

**Sprint:** S30
**Owner:** Robert Reichert (RSI Academy)
**Status:** Configuration spec — ready for Stripe dashboard + code wiring

## 1. Stripe product catalog

Create these as Stripe **Products** (one product per credential family, multiple prices per product).

| Product name | `metadata.pack_slug` | Visible to customers |
|---|---|---|
| RSI ACADEMY — CHDA Prep | `chda` | Yes |
| RSI ACADEMY — CRC Prep | `crc` | Yes |
| RSI ACADEMY — CPHQ Prep | `cphq` | Yes |
| RSI ACADEMY — MA Bundle (CRC + CHDA) | `ma_bundle` | Yes |
| RSI ACADEMY — All-Access | `all_access` | Yes |

## 2. Price objects (per product)

Each product gets 4 prices:

| Price nickname | Recurring | Amount | `metadata.tier` |
|---|---|---|---|
| Monthly Standard | month | varies | `standard` |
| Annual Standard | year | varies | `standard` |
| Monthly Founder | month | varies | `founder` |
| Annual Founder | year | varies | `founder` |

### 2.1 Per-credential pricing

| SKU | Monthly Std | Annual Std | Monthly Founder | Annual Founder |
|---|---|---|---|---|
| CHDA | $19.00 | $149.00 | $9.00 | $79.00 |
| CRC | $19.00 | $149.00 | $9.00 | $79.00 |
| CPHQ | $19.00 | $149.00 | $9.00 | $79.00 |
| MA Bundle | $29.00 | $199.00 | $19.00 | $159.00 |
| All-Access | $39.00 | $299.00 | $29.00 | $239.00 |

### 2.2 Free trial

Configure 14-day trial via `subscription.trial_period_days = 14` at Checkout session creation. Card on file required.

## 3. Founder tier enforcement

Founder tier is capped at **first 50 paying subscribers across all SKUs combined**.

### 3.1 Gate logic

```python
# rsi-academy/api/founder_gate.py
"""
Founder tier gate — caps first 50 paying subscribers across all SKUs.
Hard limit enforced via Supabase row count in `founder_seats` table.
"""
from __future__ import annotations
from supabase import Client

FOUNDER_SEAT_CAP = 50

def is_founder_available(supabase: Client) -> bool:
    """Return True if founder seats remain."""
    result = supabase.table("founder_seats").select("id", count="exact").execute()
    return (result.count or 0) < FOUNDER_SEAT_CAP

def claim_founder_seat(
    supabase: Client,
    user_email: str,
    stripe_subscription_id: str,
    pack_slug: str,
) -> bool:
    """Atomically claim a founder seat. Returns False if cap reached."""
    if not is_founder_available(supabase):
        return False
    supabase.table("founder_seats").insert({
        "email": user_email,
        "stripe_subscription_id": stripe_subscription_id,
        "pack_slug": pack_slug,
    }).execute()
    return True
```

### 3.2 Supabase schema additions

```sql
CREATE TABLE founder_seats (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email                    TEXT NOT NULL,
  stripe_subscription_id   TEXT NOT NULL UNIQUE,
  pack_slug                TEXT NOT NULL,
  claimed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  lifetime_locked          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_founder_seats_email ON founder_seats(email);

-- Backfill from existing prep_pack_access if any pre-launch grants
```

### 3.3 Checkout flow

1. User clicks "Start trial — Founder tier"
2. Landing-page JS calls `/api/founder-availability` → returns `{available: true|false, seats_remaining: N}`
3. If available, Checkout session created with founder price ID + 14-day trial
4. On `checkout.session.completed` webhook: call `claim_founder_seat()` atomically
5. If `claim_founder_seat()` returns False (race lost), refund + email + offer standard tier

## 4. Pass Guarantee

### 4.1 Customer-facing terms (Stripe metadata + FAQ)

> **RSI ACADEMY Pass Guarantee.** If you do not pass your credential exam after 90 days of regular use (defined as ≥3 study sessions per week for at least 8 weeks) and submit your score report or attestation, we will extend your subscription by 3 months at no charge.

### 4.2 Implementation

- Stripe metadata on each subscription: `pass_guarantee_eligible: true`
- Supabase `pass_guarantee_claims` table tracks claims
- Manual approval workflow (admin reviews score report or attestation)
- On approval, apply 3-month coupon via Stripe API

```sql
CREATE TABLE pass_guarantee_claims (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email                    TEXT NOT NULL,
  stripe_subscription_id   TEXT NOT NULL,
  pack_slug                TEXT NOT NULL,
  claim_submitted_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  score_report_url         TEXT,
  attestation_text         TEXT,
  approved                 BOOLEAN,
  approved_at              TIMESTAMPTZ,
  extension_applied_at     TIMESTAMPTZ,
  notes                    TEXT
);
```

## 5. Webhook handler updates

Existing `stripe-enrollment-webhook` Supabase Edge Function needs these added events:

| Event | Handler action |
|---|---|
| `checkout.session.completed` | Existing: upsert `prep_pack_access`. **Add:** if founder price, call `claim_founder_seat()` |
| `customer.subscription.updated` | New: keep `prep_pack_access.subscription_status` in sync |
| `customer.subscription.deleted` | New: set `prep_pack_access.subscription_status = 'canceled'` |
| `customer.subscription.trial_will_end` | New: trigger email reminder 2 days before trial ends |
| `invoice.payment_failed` | New: set `prep_pack_access.subscription_status = 'past_due'` |

## 6. `prep_pack_access` schema additions

```sql
ALTER TABLE prep_pack_access
  ADD COLUMN subscription_status TEXT,         -- trialing|active|past_due|canceled
  ADD COLUMN tier TEXT,                        -- standard|founder
  ADD COLUMN trial_ends_at TIMESTAMPTZ,
  ADD COLUMN current_period_end TIMESTAMPTZ;

CREATE INDEX idx_prep_pack_access_status ON prep_pack_access(subscription_status);
```

Existing unique index on `(email, pack_slug)` and `(stripe_session_id, pack_slug)` retained.

## 7. Test plan

### 7.1 Stripe test mode flow

- [ ] Create test products + prices for CHDA only initially
- [ ] Test card `4242 4242 4242 4242` — standard monthly trial → paid conversion
- [ ] Test card `4242 4242 4242 4242` — founder monthly with seat available
- [ ] Test founder gate at cap (manually insert 50 rows into `founder_seats` in test) → next checkout falls back to standard
- [ ] Test trial cancellation (trial → cancel → access revoked at trial end)
- [ ] Test failed payment (use `4000 0000 0000 0341`) → `past_due` set correctly
- [ ] Test Pass Guarantee claim submission → admin approves → 3-month extension applied

### 7.2 Production cutover checklist

- [ ] Create live mode products + prices (mirror test config)
- [ ] Update Edge Function env vars: `STRIPE_SECRET_KEY` (live), `STRIPE_WEBHOOK_SECRET` (live)
- [ ] Wire founder gate to Academy Supabase project (`iuuwevfxnqmcplxkrkbi`)
- [ ] Smoke test live mode with one real $9 founder transaction (refund after verify)
- [ ] Update landing page checkout buttons to live price IDs

## 8. Environment variables (`.env.example` additions)

```
# Stripe — live mode
STRIPE_SECRET_KEY=sk_live_REDACTED
STRIPE_WEBHOOK_SECRET=whsec_REDACTED
STRIPE_PRICE_CHDA_MONTHLY_STD=price_REDACTED
STRIPE_PRICE_CHDA_ANNUAL_STD=price_REDACTED
STRIPE_PRICE_CHDA_MONTHLY_FOUNDER=price_REDACTED
STRIPE_PRICE_CHDA_ANNUAL_FOUNDER=price_REDACTED
STRIPE_PRICE_CRC_MONTHLY_STD=price_REDACTED
STRIPE_PRICE_CRC_ANNUAL_STD=price_REDACTED
STRIPE_PRICE_CRC_MONTHLY_FOUNDER=price_REDACTED
STRIPE_PRICE_CRC_ANNUAL_FOUNDER=price_REDACTED
STRIPE_PRICE_CPHQ_MONTHLY_STD=price_REDACTED
STRIPE_PRICE_CPHQ_ANNUAL_STD=price_REDACTED
STRIPE_PRICE_CPHQ_MONTHLY_FOUNDER=price_REDACTED
STRIPE_PRICE_CPHQ_ANNUAL_FOUNDER=price_REDACTED
STRIPE_PRICE_MA_BUNDLE_MONTHLY_STD=price_REDACTED
STRIPE_PRICE_MA_BUNDLE_ANNUAL_STD=price_REDACTED
STRIPE_PRICE_MA_BUNDLE_MONTHLY_FOUNDER=price_REDACTED
STRIPE_PRICE_MA_BUNDLE_ANNUAL_FOUNDER=price_REDACTED
STRIPE_PRICE_ALL_ACCESS_MONTHLY_STD=price_REDACTED
STRIPE_PRICE_ALL_ACCESS_ANNUAL_STD=price_REDACTED
STRIPE_PRICE_ALL_ACCESS_MONTHLY_FOUNDER=price_REDACTED
STRIPE_PRICE_ALL_ACCESS_ANNUAL_FOUNDER=price_REDACTED

# Founder tier
FOUNDER_SEAT_CAP=50
```
