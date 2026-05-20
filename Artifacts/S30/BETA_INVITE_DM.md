# CHDA Beta Invite — LinkedIn DM Template

**Sprint:** S30
**Owner:** Robert Reichert (RSI Academy)
**Target audience:** CHDA-certified LinkedIn contacts (135-holder list, with priority to the 4 calibration respondents)
**Send window:** Open when Tier 1 MVP passes internal smoke + 25 beta seats are provisioned

## 1. Version A — for the 4 calibration respondents (warmest)

> Hi [First name],
>
> Quick follow-up — your CHDA exam calibration notes shaped the bank we're shipping. The mobile flashcard MVP is ready for beta and I'm holding 4 of the first 25 seats for the folks who helped with the research.
>
> Founder tier for you: $9/mo or $79/yr, lifetime price-lock. 14-day free trial. Full 300-item CHDA bank with spaced repetition, offline mode, and rationales aligned to the data governance + applied terminology emphasis you flagged.
>
> Want in? I can send a link to claim your seat — takes about 60 seconds.
>
> Robert
>
> *RSI Academy — rreichert-rsi-academy.hf.space*

## 2. Version B — for the broader 135-holder list

> Hi [First name],
>
> I noticed you're CHDA-certified — congrats. I'm a healthcare AI architect (22 years in MA analytics) and I just shipped a mobile flashcard prep app for CHDA candidates as part of RSI Academy.
>
> Opening 25 beta seats at founder pricing: $9/mo or $79/yr, lifetime locked. Spaced repetition (SM-2), full offline, sub-200ms latency, MA-flavored rationales for the D5 submissions content. 14-day free trial.
>
> If you know anyone currently studying for CHDA — or if you're considering recertification prep — would love to get them in. Reply and I'll send a direct link.
>
> Robert
>
> *RSI Academy — rreichert-rsi-academy.hf.space*
> *github.com/reichert-science-intelligence*

## 3. Version C — for CHDA-aligned role-seekers (e.g. the 4th respondent)

> Hi [First name],
>
> Thanks for the calibration notes — they're directly informing the bank we're shipping. Three things:
>
> 1. **Beta access.** Holding a founder seat for you — $9/mo or $79/yr, lifetime locked. 25 seats total. Want it?
>
> 2. **On your CHDA-aligned role search** (claims, CMS encounters, risk adjustment, population health, HEDIS) — that's exactly the space I'm in too. If I surface anything in my own pipeline that fits your profile, I'll forward. If you see anything that fits an MA analytics architect with 22 years at UPMC, Aetna, TriWest, and BCBS, same favor would be appreciated.
>
> 3. **Permission ask.** Would you be open to a public quote attribution for the calibration insight you shared about prep material scarcity? Happy to send the exact line for your review before it goes anywhere.
>
> Robert
>
> *RSI Academy — rreichert-rsi-academy.hf.space*

## 4. Follow-up cadence

- **D+0:** Initial DM
- **D+5:** Soft follow-up if no reply: *"Just bumping — beta seats filling. Still want to hold one?"*
- **D+10:** Final follow-up: *"Closing the founder window soon — last chance for $9/$79 lifetime lock."*
- **D+11+:** Move to standard pricing if they come back later

## 5. Tracking

Log each send in Supabase (Primary project `wiwmphjkupcnntawpafg`) `beta_outreach` table:

```sql
CREATE TABLE beta_outreach (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_name       TEXT NOT NULL,
  linkedin_url       TEXT,
  email              TEXT,
  variant            TEXT NOT NULL,  -- A | B | C
  sent_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  d5_followup_at     TIMESTAMPTZ,
  d10_followup_at    TIMESTAMPTZ,
  reply_received_at  TIMESTAMPTZ,
  reply_disposition  TEXT,  -- yes_beta | no | maybe | role_search_only
  seat_claimed       BOOLEAN DEFAULT FALSE,
  notes              TEXT
);
```

## 6. Anti-patterns (will not do)

- Mass blast (LinkedIn flags + damages reputation)
- Generic templating that ignores the calibration relationship
- Pressure tactics or fake scarcity
- Cold outreach to non-CHDA holders pretending it's warm
- Mentioning RSI Academy URL more than once per message
