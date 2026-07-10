# NextRupee — Brand & Design System

Source of truth: [NextRupee-Design-System.html](./NextRupee-Design-System.html) (open in a browser — it's a self-contained interactive artifact, keep `support.js` alongside it). `ios-frame.jsx` is a reusable device-frame component used for the mobile showcase section. `assets/thumbnail.webp` is the cover preview.

## Quick reference

**Tagline:** "Understand every financial decision before you make it."
**One-line pitch:** Typography-first, geometric, quiet. The mark reads as direction — never a coin or piggy bank.

### Logo
Compass-needle / ascending-arrow mark. 24px min clear-space. Use on near-black (#0B0D12) or white only — never recolor, gradient, shadow, or rotate. Minimum size: 20px on screen, 6mm print.

### Color
| Token | Hex | Use |
|---|---|---|
| Indigo 600 | `#4338CA` | Primary |
| Indigo 700 | `#372FA6` | Hover/active |
| Indigo 300 | `#B7B0F0` | Border/icon |
| Indigo 100 | `#EEECFB` | Tint/surface |
| Gold Signal | `#9C7A2E` | Gold-engine context **only** — never a generic accent |
| Ink | `#0B0D12` | Text/headings |
| Ink-2 | `#4B5163` | Body text |
| Ink-3 | `#8A8F9C` | Captions/disabled |
| Border-strong | `#D3D6DD` | Dividers |
| Border | `#E4E6EB` | Card outlines |
| Surface-2 | `#F5F6F8` | Page background |
| Success | `#15803D` on `#E7F6EC` | |
| Warning | `#B45309` on `#FDF0DE` | |
| Error | `#B42318` on `#FCEAE8` | |

### Typography
- **Space Grotesk** (500/600/700) — display & headings
- **IBM Plex Sans** (400/500/600) — body & UI text
- **IBM Plex Mono** (400/500) — numbers, evidence refs, data

Scale: Display 36–72px/600/-0.02em · Heading 20–28px/600 · Body large 17px/400 · Body 15px/400 · Evidence/mono 13–14px.

### Foundations
- **Spacing (px):** 4·8·12·16·24·32·48·64·96·128
- **Radius:** 8 chip/input · 12 card · 16 panel · 24 modal · 999 pill
- **Shadow:** sm `0 1px 2px` · md `0 4px 16px` · lg `0 12px 32px` (all rgba(11,13,18,.04–.10))
- **Grid:** 1280px max-width, 12 columns, 24px gutter, 96px section padding desktop / 24px mobile
- **Icons:** 1.6px line weight, rounded joins, 24px grid, outline only — no filled icons, no coin/piggy-bank clichés
- **Illustration:** none decorative — use real data (charts, driver graphs, evidence chips) instead

### Six design principles
1. Show the work — every figure links to the calc/doc that produced it
2. The model never computes — math is deterministic and code-owned
3. Confidence has boundaries — every recommendation states what would change it
4. One recommendation, ranked — alternatives visible but subordinate
5. Plain language over jargon
6. Calm, not clever — no countdowns, urgency copy, or gamified streaks

**Voice:** Confident, analytical, transparent. Declarative sentences, cited numbers, no exclamation marks, no emoji.

### Interaction language (key patterns)
Decision Selector · Ranked Action List · Evidence Trace · Confidence Signal · Progressive Commitment Flow · Reasoning Disclosure (fixed cascade: Decision → Evidence → Reasoning → Alternatives → Risks → Assumptions → What would change this)

### Financial input patterns
Currency Input · Percentage Input · Single-Choice Cards · Goal Selection Chips · Risk Preference Selector · Binary Decision Cards · Progressive Multi-Step Form · Financial Summary Card · Inline Guidance · Validation & Error States

The HTML artifact also covers: full component library, mobile showcase frames, user flows, and the Intelligence Engine / roadmap sections — open it directly for the complete reference.

## Related
See [../docs/NextRupee_Master_Doc.md](../docs/NextRupee_Master_Doc.md) for the product architecture, data model, and build/test/deploy plan this design system supports.
