# Personal Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a single-page personal branding site for Chandan Kumar at `https://chandan-123kumar.github.io`.

**Architecture:** Static site, plain HTML + CSS + vanilla JS, no build step, no framework. Single `index.html` with all sections (Hero / About / Projects / Experience / Content / Skills / Contact). Deployed via GitHub Pages user-site (auto-publishes from `main` branch root).

**Tech Stack:** HTML5, CSS3 (Flexbox + Grid + backdrop-filter), vanilla JavaScript (IntersectionObserver), Inter via Google Fonts. No npm, no bundler.

## Global Constraints

- Local project path: `/Users/chandankumar/Desktop/AIEngg/personal-website/` (working copy; pushed manually by user to `github.com/chandan-123kumar/chandan-123kumar.github.io`)
- No build step. No package.json. No external JS libraries.
- Palette — background `#0a0b14`, text `#e6e8ef`, secondary `#9aa3b2`, accent cyan `#22d3ee`, accent purple `#a78bfa`
- Font: Inter (Google Fonts), weights 400/500/600/700, `display=swap`
- Max content width: 1100px
- Mobile-first; breakpoints 768px (tablet) and 1024px (desktop)
- Lighthouse target ≥ 95 across Performance / Accessibility / Best Practices / SEO
- All copy verbatim from spec (`docs/superpowers/specs/2026-06-23-personal-website-design.md`)
- Resume source: `/Users/chandankumar/Desktop/img/Resume_Template_for_Software_Engineer__4_ (3).pdf` → copy to `resume.pdf`
- Real URLs to embed:
  - Email: `chandan.kumar.stack@gmail.com`
  - GitHub: `https://github.com/chandan-123kumar`
  - LinkedIn: `https://www.linkedin.com/in/chandan-kumar-100a78111/`
  - Instagram: `https://www.instagram.com/ai_system_design`
  - YouTube: `#` (placeholder)
- `prefers-reduced-motion` must disable scroll fade-ins
- Semantic HTML required (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- "Test" for this project = open `index.html` in a browser and visually verify; there is no automated test harness

---

## File Structure

```
personal-website/
├── index.html              # entire page, all sections
├── styles.css              # all styling (~400-500 lines)
├── script.js               # mobile nav, smooth-scroll, fade-in observer
├── resume.pdf              # copy of Chandan's resume
├── assets/
│   ├── favicon.svg         # simple "CK" mark on dark bg
│   └── og-image.svg        # social card (text-based placeholder)
└── README.md               # what this is + deploy instructions
```

---

### Task 1: Project scaffold & resume copy

**Files:**
- Create: `personal-website/`
- Create: `personal-website/index.html`
- Create: `personal-website/styles.css`
- Create: `personal-website/script.js`
- Create: `personal-website/README.md`
- Create: `personal-website/assets/` (directory)
- Copy:   `personal-website/resume.pdf` from `/Users/chandankumar/Desktop/img/Resume_Template_for_Software_Engineer__4_ (3).pdf`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: an empty scaffold that opens to a blank page in a browser; later tasks fill in real content

- [ ] **Step 1: Create project directory**

```bash
mkdir -p /Users/chandankumar/Desktop/AIEngg/personal-website/assets
cd /Users/chandankumar/Desktop/AIEngg/personal-website
```

- [ ] **Step 2: Copy the resume PDF**

```bash
cp "/Users/chandankumar/Desktop/img/Resume_Template_for_Software_Engineer__4_ (3).pdf" /Users/chandankumar/Desktop/AIEngg/personal-website/resume.pdf
ls -la /Users/chandankumar/Desktop/AIEngg/personal-website/resume.pdf
```

Expected: `resume.pdf` exists, ~50KB.

- [ ] **Step 3: Create minimal index.html scaffold**

`personal-website/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Chandan Kumar — Senior AI Engineer</title>
  <meta name="description" content="Senior AI Engineer building agentic systems, low-latency voice AI, and GPU-accelerated inference. BrowserStack AI Champion 2025." />
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
  <meta property="og:title" content="Chandan Kumar — Senior AI Engineer" />
  <meta property="og:description" content="Agentic systems, voice AI, GPU. BrowserStack AI Champion 2025." />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="assets/og-image.svg" />
  <meta name="twitter:card" content="summary_large_image" />
</head>
<body>
  <main></main>
  <script src="script.js" defer></script>
</body>
</html>
```

- [ ] **Step 4: Create empty styles.css and script.js**

`personal-website/styles.css`:
```css
/* styles will be added in subsequent tasks */
```

`personal-website/script.js`:
```javascript
// behavior will be added in subsequent tasks
```

- [ ] **Step 5: Create README.md**

`personal-website/README.md`:
```markdown
# chandan-123kumar.github.io

Personal website for Chandan Kumar — Senior AI Engineer.

Plain HTML + CSS + vanilla JS. No build step.

## Local preview

Open `index.html` in a browser, or run:

```
python3 -m http.server 8000
```

Then visit http://localhost:8000.

## Deploy

Push to the `main` branch of `github.com/chandan-123kumar/chandan-123kumar.github.io`. GitHub Pages auto-publishes within ~1 minute.
```

- [ ] **Step 6: Verify scaffold opens**

```bash
cd /Users/chandankumar/Desktop/AIEngg/personal-website && python3 -m http.server 8765 &
sleep 1 && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8765/
kill %1 2>/dev/null
```

Expected: `200`.

- [ ] **Step 7: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Scaffold personal website: index, css, js, resume"
```

---

### Task 2: Design tokens & base styles

**Files:**
- Modify: `personal-website/styles.css` (append base styles)

**Interfaces:**
- Consumes: Task 1's empty `styles.css`
- Produces: CSS custom properties (`--bg`, `--text`, `--text-dim`, `--accent`, `--accent-2`, `--surface`, `--border`, `--maxw`), `body` typography, gradient background blobs. Used by every later task.

- [ ] **Step 1: Replace styles.css with design tokens + base**

`personal-website/styles.css`:
```css
:root {
  --bg: #0a0b14;
  --text: #e6e8ef;
  --text-dim: #9aa3b2;
  --accent: #22d3ee;
  --accent-2: #a78bfa;
  --surface: rgba(255, 255, 255, 0.04);
  --border: rgba(255, 255, 255, 0.08);
  --maxw: 1100px;
  --radius: 14px;
  --transition: 200ms ease;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  font-weight: 400;
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
  position: relative;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 20% 10%, rgba(34, 211, 238, 0.15), transparent 40%),
    radial-gradient(circle at 80% 30%, rgba(167, 139, 250, 0.12), transparent 45%),
    radial-gradient(circle at 50% 90%, rgba(34, 211, 238, 0.08), transparent 50%);
  z-index: -1;
  pointer-events: none;
}

a { color: var(--accent); text-decoration: none; transition: opacity var(--transition); }
a:hover { opacity: 0.8; }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 4px; }

img, svg { display: block; max-width: 100%; }

h1, h2, h3 { font-weight: 700; letter-spacing: -0.02em; line-height: 1.15; }
h2 { font-size: clamp(1.75rem, 3vw, 2.5rem); margin-bottom: 1.5rem; }
h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }

p { color: var(--text-dim); }

.container {
  max-width: var(--maxw);
  margin: 0 auto;
  padding: 0 24px;
}

section {
  padding: 64px 0;
}

@media (min-width: 1024px) {
  section { padding: 96px 0; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 2: Verify visually**

Open `personal-website/index.html` in a browser. Expected: dark background, faint cyan/purple gradient blobs visible, no errors in DevTools console.

- [ ] **Step 3: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/styles.css
git commit -m "Add design tokens and base styles for personal site"
```

---

### Task 3: Sticky nav

**Files:**
- Modify: `personal-website/index.html` (insert `<header>` before `<main>`)
- Modify: `personal-website/styles.css` (append nav styles)
- Modify: `personal-website/script.js` (mobile toggle + scroll shadow)

**Interfaces:**
- Consumes: Task 2 tokens (`--bg`, `--border`, `--accent`)
- Produces: A `<header class="nav">` with `data-nav-toggle` button and `[data-nav-menu]` list. Anchors link to `#about`, `#projects`, `#experience`, `#content`, `#contact` — every later section MUST use those IDs.

- [ ] **Step 1: Add nav markup**

In `personal-website/index.html`, replace `<body>...</body>` with:
```html
<body>
  <header class="nav" id="site-nav">
    <div class="container nav-inner">
      <a href="#top" class="nav-brand">Chandan Kumar</a>
      <button class="nav-toggle" data-nav-toggle aria-label="Toggle navigation" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-menu" data-nav-menu>
        <li><a href="#about">About</a></li>
        <li><a href="#projects">Projects</a></li>
        <li><a href="#experience">Experience</a></li>
        <li><a href="#content">Content</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
    </div>
  </header>
  <main id="top"></main>
  <script src="script.js" defer></script>
</body>
```

- [ ] **Step 2: Append nav styles to styles.css**

```css
.nav {
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(10, 11, 20, 0.6);
  border-bottom: 1px solid transparent;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.nav.scrolled {
  border-bottom-color: var(--border);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}
.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}
.nav-brand {
  font-weight: 700;
  color: var(--text);
  font-size: 1rem;
}
.nav-brand:hover { opacity: 1; color: var(--accent); }
.nav-menu {
  display: none;
  list-style: none;
  gap: 28px;
}
.nav-menu a {
  color: var(--text-dim);
  font-size: 0.95rem;
  font-weight: 500;
}
.nav-menu a:hover { color: var(--text); opacity: 1; }
.nav-toggle {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 28px;
  height: 22px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.nav-toggle span {
  display: block;
  height: 2px;
  background: var(--text);
  border-radius: 2px;
  transition: transform var(--transition), opacity var(--transition);
}
.nav-toggle[aria-expanded="true"] span:nth-child(1) { transform: translateY(10px) rotate(45deg); }
.nav-toggle[aria-expanded="true"] span:nth-child(2) { opacity: 0; }
.nav-toggle[aria-expanded="true"] span:nth-child(3) { transform: translateY(-10px) rotate(-45deg); }

@media (max-width: 767px) {
  .nav-menu.open {
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 64px;
    left: 0;
    right: 0;
    background: rgba(10, 11, 20, 0.95);
    backdrop-filter: blur(12px);
    padding: 20px 24px;
    gap: 16px;
    border-bottom: 1px solid var(--border);
  }
}
@media (min-width: 768px) {
  .nav-toggle { display: none; }
  .nav-menu { display: flex; }
}
```

- [ ] **Step 3: Add nav behavior to script.js**

Replace `personal-website/script.js`:
```javascript
(function () {
  const nav = document.getElementById('site-nav');
  const toggle = document.querySelector('[data-nav-toggle]');
  const menu = document.querySelector('[data-nav-menu]');

  const setScrolled = () => {
    nav.classList.toggle('scrolled', window.scrollY > 8);
  };
  setScrolled();
  window.addEventListener('scroll', setScrolled, { passive: true });

  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });

  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
})();
```

- [ ] **Step 4: Verify in browser**

Open `index.html`. Expected: sticky bar at top, brand left, 5 menu links right (desktop) or hamburger (resize <768px). Clicking hamburger toggles menu. Scroll down: nav gets subtle shadow.

- [ ] **Step 5: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add sticky nav with mobile toggle and scroll shadow"
```

---

### Task 4: Hero section

**Files:**
- Modify: `personal-website/index.html` (insert hero inside `<main>`)
- Modify: `personal-website/styles.css` (append hero styles)

**Interfaces:**
- Consumes: Task 2 tokens; resume.pdf must exist at `./resume.pdf`
- Produces: `<section class="hero" id="top">` containing `.metrics` and `.hero-ctas`. Anchor `#top` shared with nav brand. CTA classes `.btn`, `.btn-primary`, `.btn-secondary` are introduced here and reused later.

- [ ] **Step 1: Insert hero markup**

In `personal-website/index.html`, replace `<main id="top"></main>` with:
```html
<main id="top">
  <section class="hero">
    <div class="container">
      <p class="hero-eyebrow">Senior AI Engineer — Agentic Systems, Voice AI, GPU</p>
      <h1 class="hero-name">Chandan Kumar</h1>
      <p class="hero-pitch">7+ years building production software. Now shipping low-latency voice agents, agentic developer tooling, and LLM fine-tuning.</p>
      <div class="metrics">
        <div class="metric">
          <div class="metric-value">5&times;</div>
          <div class="metric-label">TTS speedup<br><span>Qwen3-TTS megakernel</span></div>
        </div>
        <div class="metric">
          <div class="metric-value">47<span class="metric-unit">ms</span></div>
          <div class="metric-label">Time-to-first-audio<br><span>RTX 5090</span></div>
        </div>
        <div class="metric">
          <div class="metric-value">$100K<span class="metric-unit">+</span></div>
          <div class="metric-label">ARR delivered<br><span>BrowserStack</span></div>
        </div>
      </div>
      <div class="hero-ctas">
        <a class="btn btn-primary" href="resume.pdf" download>Resume</a>
        <a class="btn btn-secondary" href="https://github.com/chandan-123kumar" target="_blank" rel="noopener">GitHub</a>
        <a class="btn btn-secondary" href="#contact">Contact</a>
      </div>
    </div>
  </section>
</main>
```

- [ ] **Step 2: Append hero styles to styles.css**

```css
.hero {
  padding-top: 96px;
  padding-bottom: 64px;
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
}
.hero-eyebrow {
  color: var(--accent);
  font-size: 0.95rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 16px;
}
.hero-name {
  font-size: clamp(2.5rem, 6vw, 4.5rem);
  background: linear-gradient(135deg, var(--text) 0%, var(--accent) 60%, var(--accent-2) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 20px;
}
.hero-pitch {
  font-size: clamp(1rem, 1.6vw, 1.2rem);
  max-width: 640px;
  margin-bottom: 48px;
}
.metrics {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  margin-bottom: 40px;
}
@media (min-width: 640px) {
  .metrics { grid-template-columns: repeat(3, 1fr); gap: 20px; }
}
.metric {
  background: var(--surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}
.metric-value {
  font-size: clamp(2rem, 3.5vw, 2.75rem);
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 8px;
}
.metric-unit { font-size: 0.6em; color: var(--accent-2); }
.metric-label {
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 500;
}
.metric-label span {
  display: block;
  color: var(--text-dim);
  font-weight: 400;
  font-size: 0.85rem;
  margin-top: 2px;
}
.hero-ctas { display: flex; flex-wrap: wrap; gap: 12px; }
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 22px;
  border-radius: 999px;
  font-weight: 500;
  font-size: 0.95rem;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition), transform var(--transition);
}
.btn:hover { transform: translateY(-1px); opacity: 1; }
.btn-primary {
  background: var(--accent);
  color: #062028;
  font-weight: 600;
}
.btn-primary:hover { background: #67e8f9; }
.btn-secondary {
  background: transparent;
  color: var(--text);
  border-color: var(--border);
}
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: large gradient name, 3 metric tiles in a row (desktop) or stacked (mobile), 3 CTA buttons. Clicking "Resume" downloads `resume.pdf`.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add hero section with metrics and CTAs"
```

---

### Task 5: About + reusable section header

**Files:**
- Modify: `personal-website/index.html` (append About section after Hero)
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: Task 2 tokens, Task 3 anchor `#about`
- Produces: `.section-head` (eyebrow + h2) pattern reused in Tasks 6–9. `.badge` class introduced here, reused if needed.

- [ ] **Step 1: Insert About markup after `</section>` of hero**

```html
<section id="about" class="about">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">About</p>
      <h2>Engineer-first AI builder</h2>
    </div>
    <p class="about-body">
      Senior software engineer with 7+ years across <strong>JPMorgan Chase</strong> and <strong>BrowserStack</strong>, now building production AI — agentic developer tooling, low-latency voice agents, and LLM fine-tuning. Comfortable from GPU-level CUDA work to product delivery.
    </p>
    <p class="about-body">
      B.Tech, Electrical Engineering from <strong>IIT (BHU) Varanasi</strong> (CGPA 9.03). Mentor of two engineers and an AI-SDLC SPOC for Growth Engineering.
    </p>
    <span class="badge">BrowserStack AI Champion 2025</span>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

```css
.section-head { margin-bottom: 40px; }
.eyebrow {
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 12px;
}
.about-body {
  max-width: 720px;
  font-size: 1.05rem;
  color: var(--text);
  margin-bottom: 16px;
}
.about-body strong { color: var(--text); font-weight: 600; }
.badge {
  display: inline-block;
  margin-top: 12px;
  padding: 8px 16px;
  border: 1px solid var(--accent);
  border-radius: 999px;
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: "About" eyebrow, heading, two paragraphs, cyan-bordered AI Champion pill. Nav "About" link scrolls smoothly here.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add About section with AI Champion badge"
```

---

### Task 6: Featured Projects

**Files:**
- Modify: `personal-website/index.html`
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: `.section-head`, `.eyebrow` (Task 5); anchor `#projects`
- Produces: `.project-card` (reused only within this section), `.chips` and `.chip` (reused in Skills, Task 8)

- [ ] **Step 1: Insert Projects markup after About**

```html
<section id="projects" class="projects">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Featured Projects</p>
      <h2>What I'm shipping</h2>
    </div>
    <div class="project-grid">
      <article class="project-card">
        <h3>Qwen3-TTS Megakernel</h3>
        <p>Persistent-kernel CUDA megakernel repurposed as the talker decoder for Qwen3-TTS (0.6B). 47&nbsp;ms median TTFB and 0.145 RTF on RTX 5090 — 5&times; faster than the stock pipeline. Diagnosed and fixed a grid-barrier race deadlock; verified numerical parity against HF reference.</p>
        <div class="chips">
          <span class="chip">CUDA</span>
          <span class="chip">Qwen3-TTS</span>
          <span class="chip">bf16</span>
        </div>
        <a class="project-link" href="https://github.com/chandan-123kumar/voice_stream" target="_blank" rel="noopener">View on GitHub &rarr;</a>
      </article>

      <article class="project-card">
        <h3>Real-Time Voice Agent</h3>
        <p>Full WebSocket voice agent (mic &rarr; faster-whisper STT &rarr; gpt-4o-mini &rarr; megakernel TTS &rarr; speaker) on Pipecat with Silero VAD endpointing, barge-in, and 9 switchable voices. Cut speech-end-to-first-reply latency 2–3.7&times; to 0.7–1.1&nbsp;s by colocating STT on the GPU.</p>
        <div class="chips">
          <span class="chip">Pipecat</span>
          <span class="chip">Whisper</span>
          <span class="chip">Silero VAD</span>
        </div>
        <a class="project-link" href="https://github.com/chandan-123kumar/voice_stream" target="_blank" rel="noopener">View on GitHub &rarr;</a>
      </article>

      <article class="project-card">
        <h3>SDD Context Engine</h3>
        <p>Python FastMCP server exposing custom tools (feature-knowledge queries, dev-phase activation, mocking helpers) that injects codebase-grounded context into Claude Code / Copilot. Drives the org-wide 6-phase agentic Spec-Driven Development pipeline at BrowserStack.</p>
        <div class="chips">
          <span class="chip">FastMCP</span>
          <span class="chip">Python</span>
          <span class="chip">Claude Code</span>
        </div>
        <span class="project-link project-link--muted">BrowserStack — internal</span>
      </article>

      <article class="project-card">
        <h3>Indic LLM Fine-Tuning</h3>
        <p>Fine-tuned open-source LLMs (Qwen) for Indic languages using QLoRA. Evaluated tokenizers and compared SFT vs. continued pretraining on Indic corpora.</p>
        <div class="chips">
          <span class="chip">QLoRA</span>
          <span class="chip">Qwen</span>
          <span class="chip">SFT</span>
        </div>
        <a class="project-link" href="https://github.com/chandan-123kumar" target="_blank" rel="noopener">View on GitHub &rarr;</a>
      </article>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

```css
.project-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}
@media (min-width: 768px) {
  .project-grid { grid-template-columns: repeat(2, 1fr); gap: 24px; }
}
.project-card {
  background: var(--surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color var(--transition), transform var(--transition);
}
.project-card:hover {
  border-color: rgba(34, 211, 238, 0.4);
  transform: translateY(-2px);
}
.project-card p { color: var(--text-dim); font-size: 0.95rem; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(34, 211, 238, 0.08);
  border: 1px solid rgba(34, 211, 238, 0.2);
  color: var(--accent);
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}
.project-link {
  margin-top: auto;
  color: var(--accent);
  font-size: 0.9rem;
  font-weight: 500;
}
.project-link--muted { color: var(--text-dim); }
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: 4 glassy project cards in 2x2 grid (desktop) / stacked (mobile). Hover lifts each card slightly. Links open in new tab.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add Featured Projects section with 4 cards"
```

---

### Task 7: Experience timeline

**Files:**
- Modify: `personal-website/index.html`
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: `.section-head`, `.eyebrow`; anchor `#experience`
- Produces: `.timeline` and `.role` — used only in this section.

- [ ] **Step 1: Insert Experience markup after Projects**

```html
<section id="experience" class="experience">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Experience</p>
      <h2>Where I've worked</h2>
    </div>
    <div class="timeline">
      <article class="role">
        <header class="role-head">
          <h3>Senior Software Engineer — BrowserStack</h3>
          <span class="role-date">Oct 2024 — Present</span>
        </header>
        <ul class="role-bullets">
          <li>Drove org-wide adoption of a 6-phase agentic Spec-Driven Development pipeline — cutting dev time ~50% and story bugs up to 70% on new initiatives.</li>
          <li>Built the SDD Context Engine (Python FastMCP) and owned an agentic AI harness with 11 skills and 7 phase-specific agents.</li>
          <li>Led AI-driven Nightwatch &rarr; Playwright test migration; shipped AI code review as a deploy gate.</li>
        </ul>
      </article>

      <article class="role">
        <header class="role-head">
          <h3>Software Engineer — BrowserStack</h3>
          <span class="role-date">Mar 2022 — Sep 2024</span>
        </header>
        <ul class="role-bullets">
          <li>Built a self-serve promotional engine and upsell workflows across Pro plans; $100K+ ARR across retention initiatives.</li>
          <li>End-to-end marketing-attribution system (UTM tracking, cross-page activity, Salesforce sync).</li>
        </ul>
      </article>

      <article class="role">
        <header class="role-head">
          <h3>Associate Software Engineer — JPMorgan Chase</h3>
          <span class="role-date">Mar 2020 — Mar 2022</span>
        </header>
        <ul class="role-bullets">
          <li>Built a Spring Boot + React monitoring and alerting tool tracking 26 applications across stacks; mentored an offshore team for ~1 year.</li>
        </ul>
      </article>

      <article class="role">
        <header class="role-head">
          <h3>Software Engineer (SDE 1) — JPMorgan Chase</h3>
          <span class="role-date">Jul 2019 — Mar 2020</span>
        </header>
        <ul class="role-bullets">
          <li>Built an end-to-end Spring Boot application for the SPG mortgage-analytics platform — the entry and exit point for all securitized-product analysis at JPMC.</li>
        </ul>
      </article>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

```css
.timeline {
  display: flex;
  flex-direction: column;
  gap: 24px;
  position: relative;
  padding-left: 24px;
  border-left: 2px solid var(--border);
}
.role {
  background: var(--surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  position: relative;
}
.role::before {
  content: '';
  position: absolute;
  left: -32px;
  top: 28px;
  width: 12px;
  height: 12px;
  background: var(--accent);
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.15);
}
.role-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
@media (min-width: 640px) {
  .role-head { flex-direction: row; justify-content: space-between; align-items: baseline; gap: 16px; }
}
.role-date { color: var(--text-dim); font-size: 0.85rem; font-weight: 500; white-space: nowrap; }
.role-bullets { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.role-bullets li {
  color: var(--text-dim);
  font-size: 0.95rem;
  padding-left: 18px;
  position: relative;
}
.role-bullets li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 6px;
  height: 6px;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0.6;
}
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: vertical line on the left, 4 role cards each with a cyan dot, role title, date right-aligned (desktop) or stacked (mobile), bulleted highlights.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add Experience timeline with 4 roles"
```

---

### Task 8: Content (@ai_system_design) + Skills

**Files:**
- Modify: `personal-website/index.html`
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: `.section-head`, `.eyebrow`, `.chip`, `.btn`, `.btn-secondary`
- Produces: anchors `#content` and (in Task 9) `#contact`. `.skill-row` introduced here.

- [ ] **Step 1: Insert Content + Skills markup after Experience**

```html
<section id="content" class="content">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Content</p>
      <h2>I teach AI system design</h2>
    </div>
    <p class="content-body">
      I create AI system-design education for engineers on Instagram and YouTube — multi-agent patterns, LangChain / LangGraph / CrewAI, distributed systems, and database internals.
    </p>
    <div class="content-ctas">
      <a class="btn btn-secondary" href="https://www.instagram.com/ai_system_design" target="_blank" rel="noopener">Instagram &mdash; @ai_system_design</a>
      <a class="btn btn-secondary" href="#" target="_blank" rel="noopener">YouTube</a>
    </div>
  </div>
</section>

<section id="skills" class="skills">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Skills</p>
      <h2>What I work with</h2>
    </div>
    <div class="skill-row">
      <div class="skill-label">AI / GenAI</div>
      <div class="chips">
        <span class="chip">LLM fine-tuning (QLoRA, SFT)</span>
        <span class="chip">RAG</span>
        <span class="chip">Multi-agent systems</span>
        <span class="chip">Agentic SDLC</span>
        <span class="chip">AI code review</span>
        <span class="chip">Prompt &amp; context engineering</span>
        <span class="chip">Agent evaluation</span>
      </div>
    </div>
    <div class="skill-row">
      <div class="skill-label">Agent Frameworks</div>
      <div class="chips">
        <span class="chip">LangChain</span>
        <span class="chip">LangGraph</span>
        <span class="chip">CrewAI</span>
        <span class="chip">MCP / FastMCP</span>
      </div>
    </div>
    <div class="skill-row">
      <div class="skill-label">Voice AI</div>
      <div class="chips">
        <span class="chip">Pipecat</span>
        <span class="chip">Twilio</span>
        <span class="chip">ElevenLabs</span>
        <span class="chip">Cartesia</span>
        <span class="chip">Whisper / faster-whisper</span>
        <span class="chip">Silero VAD</span>
        <span class="chip">Qwen3-TTS</span>
      </div>
    </div>
    <div class="skill-row">
      <div class="skill-label">Languages</div>
      <div class="chips">
        <span class="chip">Python</span>
        <span class="chip">Java (Spring Boot)</span>
        <span class="chip">JavaScript / React</span>
        <span class="chip">C</span>
        <span class="chip">Bash</span>
        <span class="chip">SQL</span>
      </div>
    </div>
    <div class="skill-row">
      <div class="skill-label">Systems &amp; Infra</div>
      <div class="chips">
        <span class="chip">CUDA / GPU programming</span>
        <span class="chip">FastAPI</span>
        <span class="chip">Docker</span>
        <span class="chip">PostgreSQL</span>
        <span class="chip">Redis</span>
        <span class="chip">Kafka</span>
        <span class="chip">MongoDB</span>
        <span class="chip">AWS</span>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Append styles**

```css
.content-body { max-width: 720px; font-size: 1.05rem; color: var(--text); margin-bottom: 28px; }
.content-ctas { display: flex; flex-wrap: wrap; gap: 12px; }

.skill-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
.skill-row:last-child { border-bottom: none; }
@media (min-width: 768px) {
  .skill-row { grid-template-columns: 200px 1fr; gap: 32px; align-items: center; }
}
.skill-label {
  color: var(--text);
  font-weight: 600;
  font-size: 0.95rem;
}
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: Content section with two outline buttons; Skills section with 5 labeled rows of cyan chips. Resize to mobile — label stacks above chips.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add Content and Skills sections"
```

---

### Task 9: Footer / Contact

**Files:**
- Modify: `personal-website/index.html`
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: `.btn-primary`, `.btn-secondary`; anchor `#contact`
- Produces: site footer; this is the last visible section.

- [ ] **Step 1: Insert Contact + footer markup after Skills, before `</main>`**

```html
<section id="contact" class="contact">
  <div class="container">
    <div class="section-head">
      <p class="eyebrow">Contact</p>
      <h2>Let's talk</h2>
    </div>
    <p class="contact-pitch">Open to senior AI / GenAI roles, voice-agent work, and speaking. Fastest reply via email.</p>
    <div class="contact-ctas">
      <a class="btn btn-primary" href="mailto:chandan.kumar.stack@gmail.com">Email me</a>
      <a class="btn btn-secondary" href="resume.pdf" download>Download resume</a>
    </div>
    <ul class="contact-links">
      <li><a href="mailto:chandan.kumar.stack@gmail.com">chandan.kumar.stack@gmail.com</a></li>
      <li><a href="https://www.linkedin.com/in/chandan-kumar-100a78111/" target="_blank" rel="noopener">LinkedIn</a></li>
      <li><a href="https://github.com/chandan-123kumar" target="_blank" rel="noopener">GitHub</a></li>
      <li><a href="https://www.instagram.com/ai_system_design" target="_blank" rel="noopener">Instagram</a></li>
    </ul>
  </div>
</section>
```

Then, after `</main>`, before `<script>`:
```html
<footer class="site-footer">
  <div class="container">
    <p>&copy; 2026 Chandan Kumar</p>
  </div>
</footer>
```

- [ ] **Step 2: Append styles**

```css
.contact-pitch { max-width: 640px; font-size: 1.05rem; margin-bottom: 28px; }
.contact-ctas { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 32px; }
.contact-links {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}
.contact-links a { color: var(--text-dim); font-size: 0.95rem; }
.contact-links a:hover { color: var(--accent); }

.site-footer {
  padding: 32px 0;
  border-top: 1px solid var(--border);
}
.site-footer p { color: var(--text-dim); font-size: 0.85rem; text-align: center; }
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected: Contact section, two CTA buttons, 4 contact links in a row (wrap on mobile), footer with copyright.

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add Contact section and footer"
```

---

### Task 10: Scroll fade-in interactions

**Files:**
- Modify: `personal-website/script.js`
- Modify: `personal-website/styles.css`

**Interfaces:**
- Consumes: every `<section>` already in the DOM
- Produces: `.fade-in` initial state + `.in-view` revealed state. No new structure required in earlier tasks — the script attaches `.fade-in` at runtime.

- [ ] **Step 1: Append fade-in styles**

```css
.fade-in {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 600ms ease, transform 600ms ease;
}
.fade-in.in-view {
  opacity: 1;
  transform: translateY(0);
}
```

- [ ] **Step 2: Append observer logic to script.js**

Append to `personal-website/script.js`:
```javascript
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const sections = document.querySelectorAll('main > section');
  sections.forEach((s) => s.classList.add('fade-in'));

  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  sections.forEach((s) => obs.observe(s));
})();
```

- [ ] **Step 3: Verify in browser**

Reload `index.html`. Expected: each section fades and slides into view as you scroll. With OS "reduce motion" enabled, sections appear immediately (no transition).

- [ ] **Step 4: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add scroll fade-in interactions with reduced-motion fallback"
```

---

### Task 11: Favicon, OG image, polish & Lighthouse check

**Files:**
- Create: `personal-website/assets/favicon.svg`
- Create: `personal-website/assets/og-image.svg`
- Modify: `personal-website/README.md` (deploy note)

**Interfaces:**
- Consumes: existing markup; replaces placeholder asset references
- Produces: final shippable site

- [ ] **Step 1: Create favicon.svg**

`personal-website/assets/favicon.svg`:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0a0b14"/>
  <text x="50%" y="50%" font-family="Inter, system-ui, sans-serif" font-size="32" font-weight="700"
        fill="#22d3ee" text-anchor="middle" dominant-baseline="central">CK</text>
</svg>
```

- [ ] **Step 2: Create og-image.svg (1200x630 social card)**

`personal-website/assets/og-image.svg`:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
  <defs>
    <radialGradient id="g1" cx="20%" cy="20%" r="60%">
      <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" cx="80%" cy="80%" r="60%">
      <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#a78bfa" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="#0a0b14"/>
  <rect width="1200" height="630" fill="url(#g1)"/>
  <rect width="1200" height="630" fill="url(#g2)"/>
  <text x="80" y="290" font-family="Inter, sans-serif" font-size="84" font-weight="700" fill="#e6e8ef">Chandan Kumar</text>
  <text x="80" y="360" font-family="Inter, sans-serif" font-size="34" font-weight="500" fill="#22d3ee">Senior AI Engineer</text>
  <text x="80" y="410" font-family="Inter, sans-serif" font-size="28" font-weight="400" fill="#9aa3b2">Agentic Systems · Voice AI · GPU</text>
  <text x="80" y="530" font-family="Inter, sans-serif" font-size="22" font-weight="500" fill="#9aa3b2">5× TTS speedup · 47ms TTFB · $100K+ ARR</text>
</svg>
```

- [ ] **Step 3: Update README with deploy instructions**

Replace `personal-website/README.md`:
```markdown
# chandan-123kumar.github.io

Personal website for Chandan Kumar — Senior AI Engineer.

Plain HTML + CSS + vanilla JS. No build step.

## Local preview

```
cd personal-website
python3 -m http.server 8000
```

Open http://localhost:8000.

## Deploy

1. Create a new GitHub repository named `chandan-123kumar.github.io` (user site — name must match your GitHub username).
2. From this directory:
   ```
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin git@github.com:chandan-123kumar/chandan-123kumar.github.io.git
   git push -u origin main
   ```
3. GitHub Pages auto-publishes from `main`. Visit https://chandan-123kumar.github.io within ~1 minute.

## Editing

- Copy: edit `index.html`.
- Visual style: edit CSS custom properties in `styles.css`.
- Resume PDF: replace `resume.pdf`.
- YouTube URL: search `script.js` and `index.html` for `href="#"` and update.
```

- [ ] **Step 4: Visual QA pass in browser**

Open `index.html`. Walk through this checklist:

- [ ] Hero renders with gradient name, 3 metric tiles, 3 buttons
- [ ] "Resume" downloads `resume.pdf`
- [ ] All nav links scroll smoothly to their sections
- [ ] Sections fade in on scroll
- [ ] Mobile view (resize to ~375px): nav collapses to hamburger, metric tiles stack, project cards stack, skill rows stack
- [ ] No console errors
- [ ] Favicon shows in browser tab
- [ ] Tab through page with keyboard — every link/button shows a visible focus outline

- [ ] **Step 5: Run Lighthouse**

In Chrome DevTools → Lighthouse → Mobile, Performance + Accessibility + Best Practices + SEO. Expected: all four ≥ 95.

If any score < 95, fix issues before committing (typical fixes: missing `alt`, missing `lang`, low-contrast color — adjust tokens).

- [ ] **Step 6: Commit**

```bash
cd /Users/chandankumar/Desktop/AIEngg
git add personal-website/
git commit -m "Add favicon, OG image, deploy README"
```

---

## Self-Review

**Spec coverage check:**
- Hero with metric tiles & CTAs → Task 4 ✓
- About + AI Champion badge → Task 5 ✓
- 4 Featured Projects → Task 6 ✓
- Experience timeline (4 roles) → Task 7 ✓
- Content (@ai_system_design) → Task 8 ✓
- Skills (5 grouped rows) → Task 8 ✓
- Contact footer → Task 9 ✓
- Scroll fade-in + reduced-motion → Task 10 ✓
- Favicon + OG image + SEO meta → Tasks 1 + 11 ✓
- Resume PDF download → Tasks 1 + 4 ✓
- GitHub Pages deploy instructions → Task 11 ✓
- Mobile-first responsive (breakpoints 768/1024) → all tasks ✓
- Lighthouse ≥ 95 → Task 11 verification ✓

**No placeholders:** All copy is final; only the YouTube URL is intentionally `#` per user decision.

**Type / class consistency:** `.btn / .btn-primary / .btn-secondary` introduced in Task 4 and reused in 8 and 9. `.chip / .chips` introduced in Task 6 and reused in Task 8. `.section-head / .eyebrow` introduced in Task 5 and reused in 6–9. Anchors `#top, #about, #projects, #experience, #content, #contact` match nav links in Task 3.
