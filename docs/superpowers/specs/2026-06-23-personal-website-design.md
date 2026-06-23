# Personal Website — Chandan Kumar

**Date:** 2026-06-23
**Status:** Approved (design phase)
**Owner:** Chandan Kumar

## Goal

Ship a single-page personal branding site that positions Chandan Kumar as a Senior AI Engineer (agentic systems, voice AI, GPU). Hybrid showcase: AI/voice-agent projects lead, experience and content follow. Live at `https://chandan-123kumar.github.io`.

## Audience

Recruiters, hiring managers, conference organizers, and followers from `@ai_system_design` (Instagram/YouTube). Visitors should grasp the value proposition within 5 seconds of landing.

## Non-Goals (YAGNI)

- No blog or CMS
- No analytics
- No contact-form backend (mailto: only)
- No dark/light theme toggle
- No build step, no framework, no package.json
- No custom domain (deferred — can be added later via CNAME)

## Tech Stack

- **Plain HTML5 + CSS3 + vanilla JavaScript** (no framework, no build)
- **Hosting:** GitHub Pages user site (`chandan-123kumar.github.io` repo, deploys from `main`)
- **Fonts:** Inter (Google Fonts) — variable weights 400/500/600/700
- **No external JS libraries.** IntersectionObserver is native.

## File Layout

```
chandan-123kumar.github.io/
├── index.html
├── styles.css
├── script.js
├── resume.pdf            # copied from /Users/chandankumar/Desktop/img/...
├── assets/
│   ├── favicon.svg
│   └── og-image.png      # 1200x630 social card (can be placeholder initially)
└── README.md             # short: what this is, how to deploy
```

## Visual Design

**Style:** Dark gradient AI-startup. Deep navy/black base with subtle blue→purple radial gradients. Glassy (translucent + backdrop-blur) cards. One accent color: electric cyan (`#22d3ee` family). Inter font throughout.

**Palette:**
- Background base: `#0a0b14` (near-black with blue tint)
- Surface (cards): `rgba(255,255,255,0.04)` with `backdrop-filter: blur(12px)` and `border: 1px solid rgba(255,255,255,0.08)`
- Text primary: `#e6e8ef`
- Text secondary: `#9aa3b2`
- Accent: `#22d3ee` (cyan), with `#a78bfa` (purple) for gradient highlights
- Gradient: radial blobs of `rgba(34,211,238,0.15)` and `rgba(167,139,250,0.12)` behind hero

**Typography:**
- Headings: Inter 600/700, tight tracking
- Body: Inter 400, 1.6 line-height
- Hero name: clamp(2.5rem, 6vw, 4.5rem)
- Section headings: clamp(1.75rem, 3vw, 2.5rem)

**Spacing & layout:**
- Max content width: 1100px, centered
- Section vertical padding: 96px desktop, 64px mobile
- Mobile-first; breakpoints at 768px and 1024px

## Sections

### 1. Sticky Nav
- Left: "Chandan Kumar" wordmark
- Right (desktop): About · Projects · Experience · Content · Contact
- Mobile: hamburger toggling a slide-down menu
- Background: blurred glassy on scroll
- Smooth-scroll to anchors

### 2. Hero
- H1: **Chandan Kumar**
- Subhead: **Senior AI Engineer — Agentic Systems, Voice AI, GPU**
- One-line pitch: "7+ years building production software. Now shipping low-latency voice agents, agentic developer tooling, and LLM fine-tuning."
- Three metric tiles in a row (stack on mobile):
  - `5×` — TTS speedup (Qwen3-TTS megakernel)
  - `47ms` — Time-to-first-audio
  - `$100K+` — ARR delivered
- CTAs:
  - Primary: **Resume** → downloads `resume.pdf`
  - Secondary: **GitHub** → `https://github.com/chandan-123kumar`
  - Secondary: **Contact** → smooth-scroll to footer

### 3. About
- Heading: "About"
- 2-3 sentence pitch covering: senior eng (JPMC + BrowserStack), AI Champion 2025, what he builds today, IIT BHU EE background
- Small badge/pill: "🏆 BrowserStack AI Champion 2025" (use text/emoji — no actual emoji unless approved; replace with text "AI Champion 2025" inside an accent-bordered pill)

### 4. Featured Projects
Heading: "Featured Projects". 4 glassy cards in a 2-column grid (1-column on mobile).

Each card: title, 1-line description, tech chip row, link.

1. **Qwen3-TTS Megakernel** — Persistent-kernel CUDA megakernel as talker decoder; 5× faster than stock pipeline on RTX 5090. Chips: `CUDA`, `Qwen3-TTS`, `bf16`. Link: github voice_stream repo.
2. **Real-Time Voice Agent** — WebSocket voice agent (Pipecat + faster-whisper + gpt-4o-mini + megakernel TTS); 0.7–1.1s speech-to-reply. Chips: `Pipecat`, `Whisper`, `Silero VAD`. Link: voice_stream repo.
3. **SDD Context Engine** — Python FastMCP server that injects codebase-grounded context into Claude Code/Copilot; reduces hallucination. Driving 6-phase agentic SDD pipeline at BrowserStack. Chips: `FastMCP`, `Python`, `Claude Code`. Link: (no public link — show as "BrowserStack — internal")
4. **Indic LLM Fine-Tuning** — Fine-tuned Qwen for Indic languages with QLoRA; SFT vs. continued pretraining evaluation. Chips: `QLoRA`, `Qwen`, `SFT`. Link: github.

### 5. Experience
Heading: "Experience". Vertical timeline (left-aligned accent line, role cards stack right).

1. **Senior Software Engineer, BrowserStack** — Oct 2024–Present
   - Drove org-wide 6-phase agentic SDD pipeline; cut dev time ~50%, story bugs up to 70%
   - Built SDD Context Engine (FastMCP); owned 11-skill agentic harness with 7 phase agents
   - Led AI-driven Nightwatch→Playwright migration; shipped AI code review as deploy gate
2. **Software Engineer, BrowserStack** — Mar 2022–Sep 2024
   - Built self-serve promotional engine and upsell workflows; $100K+ ARR across initiatives
   - End-to-end marketing-attribution system (UTM + Salesforce sync)
3. **Associate Software Engineer, JPMorgan Chase** — Mar 2020–Mar 2022
   - Spring Boot + React monitoring tool tracking 26 applications; mentored offshore team
4. **Software Engineer (SDE 1), JPMorgan Chase** — Jul 2019–Mar 2020
   - SPG mortgage-analytics platform — entry/exit point for all securitized-product analysis

### 6. Content / @ai_system_design
- Heading: "I teach AI system design"
- 1-2 sentences: "I create AI system-design education for engineers — multi-agent patterns, LangGraph/CrewAI, distributed systems, database internals."
- Two large buttons: **Instagram @ai_system_design** and **YouTube** (use placeholder YouTube URL if unknown — flag during impl)

### 7. Skills
Heading: "Skills". 5 rows, each labeled, with chips:
- **AI / GenAI:** LLM fine-tuning (QLoRA, SFT), RAG, multi-agent systems, agentic SDLC, AI code review, prompt & context engineering, agent evaluation
- **Agent Frameworks:** LangChain, LangGraph, CrewAI, MCP / FastMCP
- **Voice AI:** Pipecat, Twilio, ElevenLabs, Cartesia, Whisper / faster-whisper, Silero VAD, Qwen3-TTS
- **Languages:** Python, Java (Spring Boot), JavaScript / React, C, Bash, SQL
- **Systems & Infra:** CUDA / GPU programming, FastAPI, Docker, PostgreSQL, Redis, Kafka, MongoDB, AWS

### 8. Footer / Contact
- Heading: "Let's talk"
- Email: `chandan.kumar.stack@gmail.com` (mailto link)
- LinkedIn (URL TBD — use placeholder "https://www.linkedin.com/in/chandan-kumar/" and let user correct)
- GitHub: `https://github.com/chandan-123kumar`
- Instagram: `https://www.instagram.com/ai_system_design`
- Resume PDF download link
- Tiny credit line: "© 2026 Chandan Kumar"

## Interactivity (script.js)

1. **Mobile nav toggle** — hamburger opens/closes
2. **Smooth-scroll** — anchor clicks scroll smoothly
3. **Scroll-shadow on nav** — adds subtle shadow when `scrollY > 8`
4. **Fade-in on scroll** — IntersectionObserver adds `.in-view` to sections; CSS handles opacity/translateY transition. One-shot (no re-trigger).

No other JS. No event tracking. No external scripts.

## Accessibility

- Semantic HTML (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`, headings in order)
- All interactive elements keyboard-reachable; visible focus rings
- Color contrast ≥ WCAG AA on all text
- `prefers-reduced-motion` disables fade-in transitions
- `alt` text on images; `aria-label` on icon-only links

## SEO / Social

- `<title>`: "Chandan Kumar — Senior AI Engineer"
- Meta description: 1-sentence pitch
- OpenGraph + Twitter card meta tags pointing to `assets/og-image.png`
- `<link rel="canonical">`
- Favicon (SVG)

## Performance Targets

- No build, no JS frameworks → expected Lighthouse ≥ 95 on Performance, Accessibility, Best Practices, SEO
- Inter loaded via Google Fonts with `display=swap` and preconnect
- Inline critical CSS not required at this size; single stylesheet is fine

## Deployment

1. Repo: `chandan-123kumar/chandan-123kumar.github.io` on GitHub (user site)
2. GitHub Pages auto-publishes from `main` branch root
3. Live URL: `https://chandan-123kumar.github.io` within ~1 min of push
4. **Claude will not push.** Implementation creates the local repo and commits; user pushes.

## Open Items For User Confirmation During Implementation

- Exact LinkedIn URL (placeholder used until provided)
- YouTube channel URL (placeholder used until provided)
- About-section copy: 2-3 sentences — implementation will draft; user reviews
- og-image: ship a simple text-based placeholder; user can replace later

## Success Criteria

- Site renders correctly on mobile (≤375px), tablet (768px), desktop (≥1024px)
- All links work; resume.pdf downloads
- Lighthouse score ≥ 95 across all four categories
- Page weight under 300KB excluding the PDF
- Loads in under 1.5s on 4G
