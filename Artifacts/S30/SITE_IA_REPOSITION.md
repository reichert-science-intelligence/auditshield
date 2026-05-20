# RSI ACADEMY — Site IA Reposition (Prep-First)

**Sprint:** S30
**Owner:** Robert Reichert (RSI Academy)
**Status:** Wireframe spec — ready for implementation in S30 Weeks 3-4
**Ship dependency:** None — can ship ahead of flashcard MVP

## 1. Strategic intent

Reposition the RSI ACADEMY landing page from "Healthcare AI Architect portfolio first" to "Prep products first, architect credibility second." The portfolio remains accessible and recruiter-discoverable, but the primary commercial surface is now the four prep products (CHDA, CRC, CPHQ, MA Bundle).

## 2. Hierarchy (top to bottom)

```
┌──────────────────────────────────────────────────────┐
│ NAV: [logo] RSI ACADEMY    [Products] [About] [Login]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  HERO BAND                                           │
│  ─────────                                           │
│  Mobile-first healthcare credentialing prep.         │
│  Built by an analytics architect.                    │
│                                                      │
│  22 years of MA analytics. Now in a flashcard.     │
│                                                      │
│  [ Start 14-day free trial — CHDA ]                  │
│  About the founder →                                 │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  PRODUCT SELECTOR                                    │
│  ────────────────                                    │
│  Pick your credential                                │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ CHDA     │  │ CRC      │  │ CPHQ     │  │ MA    │ │
│  │ BETA     │  │ COMING   │  │ COMING   │  │ BUNDLE│ │
│  │          │  │ S31      │  │ S31      │  │       │ │
│  │ $9/mo    │  │ Notify   │  │ Notify   │  │ Save  │ │
│  │ founder  │  │ me       │  │ me       │  │ $9/mo │ │
│  │ tier     │  │          │  │          │  │       │ │
│  │ [Trial]  │  │ [Email]  │  │ [Email]  │  │[Wait] │ │
│  └──────────┘  └──────────┘  └──────────┘  └───────┘ │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  WHY RSI                                             │
│  ───────                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Mobile-native│ │ Built by an  │ │ Pass         │  │
│  │ flashcard    │ │ MA analytics │ │ Guarantee    │  │
│  │ format       │ │ architect    │ │              │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  SOCIAL PROOF                                        │
│  ────────────                                        │
│  "There really aren't many prep materials available  │
│  for the CHDA exam, so what you're building makes    │
│  a lot of sense."                                    │
│  — CHDA holder, healthcare data analytics            │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ABOUT THE FOUNDER                                   │
│  ─────────────────                                   │
│  Robert Reichert — Healthcare AI Architect           │
│  22+ years Medicare Advantage analytics              │
│  UPMC · Aetna · TriWest · BCBS · MBA                 │
│                                                      │
│  [View portfolio: AuditShield · StarGuard ·          │
│   SovereignShield]                                   │
│  github.com/reichert-science-intelligence             │
│                                                      │
├──────────────────────────────────────────────────────┤
│  FOOTER                                              │
│  Terms · Privacy · Contact · GitHub                  │
└──────────────────────────────────────────────────────┘
```

## 3. Copy lockup

### 3.1 Hero
- **Headline:** Mobile-first healthcare credentialing prep. Built by an analytics architect.
- **Sub:** 22 years of MA analytics. Now in a flashcard.
- **Primary CTA:** Start 14-day free trial — CHDA
- **Secondary text link:** About the founder

### 3.2 Product cards (CHDA example, ship-ready)

```
CHDA — Certified Health Data Analyst
─────────────────────────────────────
Status: BETA — 25 seats
300 items · 6 domains · MA-flavored rationales

Founder tier (first 50 only):
$9/mo or $79/yr — lifetime locked

14-day free trial · Pass Guarantee

[ Start trial ]
```

CRC, CPHQ — replace with "COMING S31 — join waitlist" + email capture.

MA Bundle:
```
MA Bundle — CRC + CHDA
──────────────────────
Status: COMING S31
Save $9/mo vs separate subscriptions

$29/mo or $199/yr standard
Founder: $19/mo or $159/yr (first 50)

[ Notify me ]
```

### 3.3 Why RSI tiles

| Tile | Headline | Sub |
|---|---|---|
| 1 | Mobile-native flashcard format | Swipe to study. Offline. Sub-200ms taps. Built for commute and lunch breaks. |
| 2 | Built by an MA analytics architect | 22 years across UPMC, Aetna, TriWest, BCBS. Real credentials, real exam patterns. |
| 3 | Pass Guarantee | Don't pass after 90 days of regular use? 3 months free. |

### 3.4 About the founder band

> **Robert Reichert** — Healthcare AI Architect
>
> 22+ years Medicare Advantage analytics. Manager of Healthcare AI/Analytics at UPMC (2018–2024). MBA. Currently shipping the RSI portfolio: AuditShield (RADV audit defense), StarGuard (HEDIS/Star Ratings forecasting), SovereignShield (compliance intelligence).
>
> [View full portfolio →]

## 4. Implementation checklist

### 4.1 Files to modify

- [ ] `rsi-academy/app.py` — landing route serves new layout
- [ ] `rsi-academy/templates/landing.html` — new structure (or Shiny UI equivalent if pure-Python)
- [ ] `rsi-academy/static/css/landing.css` — new styles (mobile-first)
- [ ] `rsi-academy/static/js/landing.js` — product card interactions, email-capture form

### 4.2 Mobile-first CSS targets

- Single-column stack below 768px viewport
- Product cards full-width on mobile, 4-column grid above 1024px
- Hero CTA tap target ≥48px height
- All buttons WCAG AAA contrast
- Font sizes: 16px body min, 24px sub, 36-48px headline

### 4.3 Email capture (CRC, CPHQ, MA Bundle waitlists)

```sql
CREATE TABLE prep_waitlist (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT NOT NULL,
  pack_slug     TEXT NOT NULL,
  joined_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  notified_at   TIMESTAMPTZ,
  UNIQUE (email, pack_slug)
);
```

### 4.4 QR code destination

`tinyurl.com/bdevpdz5` continues to resolve to the landing root. Post-reposition, the QR experience for resume scanners becomes:

1. Recruiter scans QR
2. Lands on prep-first hero
3. Scrolls to "About the founder" band (or clicks secondary nav)
4. Sees architect credentials + portfolio links
5. Reaches GitHub via portfolio link or footer

Net: recruiter discovery path lengthens by ~1 scroll, but architect credibility is amplified by visible commercial product.

## 5. Pre-flight checklist before merge

- [ ] Mobile real-device check: iPhone Safari + Android Chrome
- [ ] Lighthouse score ≥90 performance, ≥95 accessibility
- [ ] All CTAs route to functional endpoints (no 404s)
- [ ] Email capture writes to `prep_waitlist`
- [ ] Founder seat counter visible only when seats remain
- [ ] Calibration quote published only after attribution permission received
- [ ] Portfolio link routes work (AuditShield, StarGuard, SovereignShield)
- [ ] Footer GitHub link uses `github.com/reichert-science-intelligence`
- [ ] No personal-lane content anywhere on the page

## 6. Out of scope for v1 reposition

- A/B testing infrastructure (defer to S32+)
- Blog/content marketing surface
- Customer testimonials carousel (only one quote currently; defer)
- Pricing comparison table vs Pocket Prep/Brainscape (defer)
- Multi-language (anti-feature per spec)
