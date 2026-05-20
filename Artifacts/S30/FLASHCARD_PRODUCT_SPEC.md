# RSI ACADEMY Flashcard Product Spec — CHDA Beta (and forward)

**Sprint:** S30
**Owner:** Robert Reichert (RSI Academy)
**Ship target:** Mid-June 2026 (CHDA beta, 25 seats)
**Status:** Draft v1 — for execution

## 1. Vision

RSI ACADEMY ships a mobile-native, offline-capable flashcard study app for healthcare credentialing exams, beginning with CHDA. Card-based interaction with swipe gestures, spaced repetition via SM-2, and exam-aligned content authored by a working healthcare AI architect. The product replaces ad-hoc ChatGPT-as-tutor workflows and PDF flashcards with a coherent, science-backed study system.

## 2. Target user (CHDA beta cohort)

- **Profile:** working healthcare data professionals (claims, risk adjustment, population health, HEDIS, BI) preparing for AHIMA CHDA certification
- **Context:** study during commute, lunch, between meetings — minutes, not hours
- **Device:** primary mobile (iPhone Safari, Android Chrome), secondary desktop
- **Pain points (validated by calibration respondents):** sparse prep market, ChatGPT lacks structure, AHIMA prep book is dense and non-interactive, no spaced repetition in existing options

## 3. Product surfaces — phased

| Surface | Sprint | Status |
|---|---|---|
| CHDA flashcard MVP | S30 | In spec (this doc) |
| CRC flashcard | S31 | Planned, migrates CHDA pattern |
| CPHQ flashcard | S31 | Planned, migrates CHDA pattern |
| MA Bundle (CRC + CHDA) | S31 | Planned, unified dashboard |
| All-access tier | S32 | Planned |
| RAG drift analyzer (admin) | S31 | Planned (Scope 1) |

## 4. Architecture

**Pattern:** Hybrid Shiny chrome + client-side JS card layer.

- **Shiny (Python):** auth, paywall gate, admin, Supabase queries, Stripe webhook handling, subscription state, MA-flavored content rendering
- **Client-side JS:** card UX, gesture handling (Hammer.js — see ADR-001), SM-2 calculations, IndexedDB cache management, haptic feedback
- **Backend:** Supabase (Academy project `iuuwevfxnqmcplxkrkbi`), Stripe, HuggingFace Spaces hosting

**Data flow:**

1. Authenticated user loads CHDA route
2. Shiny verifies subscription via `prep_pack_access` upsert
3. Shiny hands off to client JS with bank URL + session token
4. Client JS fetches full 300-item bank, seeds IndexedDB
5. All subsequent card interactions are client-side (sub-200ms)
6. Progress synced back to Supabase every N swipes or session end

## 5. UX specification

### 5.1 Card states

| State | Visual | Trigger |
|---|---|---|
| Question | Front face — stem + 4 options (or true/false), no rationale | Default |
| Flipped | Back face — correct answer highlighted + rationale | Tap or swipe-up |
| Dismissed-known | Card exits right with green flash | Swipe-right (ease=easy) |
| Dismissed-review | Card exits left with amber flash | Swipe-left (ease=hard) |
| Next card | Slides in from bottom | After dismiss |

### 5.2 Gesture map (locked per Tier 1 trim — 3-state input)

| Gesture | Action | SM-2 grade |
|---|---|---|
| Tap card center | Flip (peek answer, no grade) | — |
| Swipe up | Flip (mirrors tap) | — |
| Swipe right | Dismiss as known | 5 (easy) |
| Swipe left | Dismiss as needs-review | 2 (hard) |
| Long-press | Open card menu (notes, flag, skip) | — |

Note: 1–5 explicit-grade scale deferred to Tier 2 ("explicit grading mode") per S30 trim.

### 5.3 Thresholds

| Param | Value | Rationale |
|---|---|---|
| Swipe distance trigger | 50px | Below = bounce back |
| Swipe velocity trigger | 0.3px/ms | Below = bounce back |
| Angle tolerance | ±30° from horizontal | Beyond = treated as vertical |
| Flip animation duration | 300ms | Perceived smooth, not laggy |
| Card-exit animation duration | 200ms | Snappy |
| Sub-render budget | 200ms | First-tap to visible response |

### 5.4 Visual modes

- **Default:** light mode, full chrome (progress bar, domain tag, card counter)
- **Dark mode:** `prefers-color-scheme: dark` auto-detect + manual toggle
- **No-distractions mode:** stripped UI — card only, no chrome, manual exit via tap top-corner

### 5.5 Haptic feedback

- Swipe trigger: `navigator.vibrate(10)`
- Correct answer reveal: `navigator.vibrate([10, 30, 10])`
- iOS Safari fallback: silent (Vibration API unsupported); rely on animation feedback

## 6. SM-2 algorithm spec

Per the Piotr Wozniak SuperMemo 2 algorithm, simplified:

```
Inputs per card per swipe:
  ease_factor (EF), default 2.5
  interval (I), default 0 (new card)
  repetitions (n), default 0
  grade (q), from swipe: 5=right, 2=left, peek=no update

Update rules (only on swipe-right or swipe-left):
  if q < 3:
    n = 0
    I = 1
  else:
    if n == 0: I = 1
    elif n == 1: I = 6
    else: I = round(I * EF)
    n += 1

  EF = max(1.3, EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))

Next review: now + I days
```

Storage: per-card progress row in IndexedDB `progress` store, synced to Supabase `card_progress` table on session end.

## 7. Data model

### 7.1 IndexedDB (client)

```
Database: rsi-academy-chda

Store: cards
  Key: card_id (string)
  Value: { id, domain, bloom, question, options, answer, rationale, tags }

Store: progress
  Key: card_id
  Value: { ease_factor, interval, repetitions, last_seen, next_review, history[] }

Store: meta
  Key: 'session'
  Value: { user_id, pack_slug, last_sync, app_version }
```

### 7.2 Supabase (server)

```sql
CREATE TABLE card_progress (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id),
  pack_slug       TEXT NOT NULL,
  card_id         TEXT NOT NULL,
  ease_factor     NUMERIC(3,2) NOT NULL DEFAULT 2.5,
  interval_days   INTEGER NOT NULL DEFAULT 0,
  repetitions     INTEGER NOT NULL DEFAULT 0,
  last_seen       TIMESTAMPTZ,
  next_review     TIMESTAMPTZ,
  total_swipes    INTEGER NOT NULL DEFAULT 0,
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, pack_slug, card_id)
);

CREATE INDEX idx_card_progress_user_pack ON card_progress(user_id, pack_slug);
CREATE INDEX idx_card_progress_next_review ON card_progress(user_id, next_review);
```

## 8. Scope tiers (locked from prior session + S30 trim)

### Tier 1 — MVP (Weeks 3-4)

1. Sub-200ms tap latency (architectural)
2. Full offline (entire bank cached, including pre-cache)
3. Single-thumb swipe operation (3-state — up=flip, right=easy, left=hard)
4. SM-2 spaced repetition with 3-state input
5. Haptic feedback
6. Dark mode + system-aware
7. No-distractions mode
8. MA-flavored rationales (CHDA D5)
9. Pass Guarantee posture (FAQ + Stripe terms only)

### Tier 2 — Phase 2 (S31)

- Explicit 1–5 grading mode (toggle in settings)
- Mistake analytics + diagnostic depth
- Confidence-mastery calibration flagging
- Exam-day simulator (timed, randomized)
- Readiness predictor (calibrated by beta data)
- "Why is this wrong?" on-demand AI explanation (token-budgeted)
- Concept linking via semantic search
- Cross-credential reinforcement (MA Bundle)
- Unified MA Bundle dashboard

### Tier 3 — Long-term moat (S32+)

- Live RAG content updates from AHIMA/NAHQ outlines
- Job task overlay (exam-to-real-world tagging)
- CE integration for CPHQ post-pass
- Audio mode (commute)
- Per-user notes + annotations

### Anti-features (will not build)

- Streak/gamification (Duolingo trap)
- User-generated cards
- Social/discussion features
- AI chatbot as primary UX
- Video lessons
- Multi-language UI
- Aggressive email cadence

## 9. Pricing integration

Per locked structure (subscription model):

| SKU | Monthly | Annual | Founder (first 50) |
|---|---|---|---|
| CHDA | $19 | $149 | $9/mo or $79/yr (lifetime lock) |
| CRC | $19 | $149 | $9/mo or $79/yr |
| CPHQ | $19 | $149 | $9/mo or $79/yr |
| MA Bundle | $29 | $199 | tbd |
| All-access | $39 | $299 | tbd |

14-day free trial standard. Pass Guarantee: "Don't pass after 90 days of regular use? 3 months free."

See `Artifacts/S30/STRIPE_SKU_SCAFFOLD.md` for implementation.

## 10. Success metrics (beta)

| Metric | Target | Measurement |
|---|---|---|
| Beta seats filled | 25 of 25 | Supabase enrollment count |
| 14-day trial → paid conversion | ≥30% | Stripe webhook |
| 30-day retention | ≥60% | session activity ≥3x/week |
| NPS | ≥40 | post-session form |
| Pass rate (self-reported) | ≥75% | post-exam form |
| Sub-200ms tap latency (P95) | 100% sessions | client telemetry |
| Crash rate | <0.5% sessions | client error log |

## 11. Open questions

1. Should the 14-day trial require credit card up-front, or be card-less? **Recommendation:** card up-front, reduces tire-kicking, standard SaaS practice.
2. Founder tier cutoff mechanism — soft (manual close at 50) or hard (Stripe metadata count)? **Recommendation:** hard via Supabase row count gate.
3. Do MA Bundle subscribers get founder pricing on the bundle SKU too? **Recommendation:** yes, $19/mo or $159/yr bundle founder tier.
4. Pass Guarantee verification — score report upload, attestation, or honor system? **Recommendation:** attestation form with score report optional upload.

## 12. Cross-references

- `Artifacts/S30/SITE_IA_REPOSITION.md` — landing page reposition
- `Artifacts/S30/STRIPE_SKU_SCAFFOLD.md` — pricing implementation
- `Artifacts/S30/BANK_AUDIT_DATA_GOVERNANCE.md` — content audit
- `Artifacts/S30/BETA_INVITE_DM.md` — outreach template
- `Artifacts/S29/ISSUE-003_FIX_DESIGN.md` — sev-1 fix (blocks S30 start)
