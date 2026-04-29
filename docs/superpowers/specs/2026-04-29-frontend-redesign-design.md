# ADR: Frontend Redesign — React SPA

**Date:** 2026-04-29
**Status:** Approved
**Author:** Emiliano (brainstormed with Claude)

---

## Context

The current Second Brain frontend is built with Jinja2 server-side templates, vanilla JavaScript, and a custom retro phosphor-terminal CSS aesthetic (green on black, CRT scanlines, VT323 font). While functional, the design is dated and the vanilla JS approach makes it difficult to add the modern animations and interactions the product deserves.

The goal is a complete frontend rewrite that:
- Drops the retro aesthetic in favour of a modern, clean, light design
- Adds expressive animations with spring physics
- Improves the navigation UX with a top bar and command palette
- Keeps the FastAPI backend unchanged (minimal additions only)

---

## Decision

Replace the Jinja2 + vanilla JS frontend with a **React SPA** built with **Vite**, using **TanStack Router** for type-safe routing and **TanStack Query** for server state, animated with **Framer Motion**.

### Stack

| Concern | Choice | Rationale |
|---|---|---|
| Bundler | Vite 6 | Zero-config, HMR, native ESM |
| Framework | React 19 | Industry standard, Framer Motion ecosystem |
| Routing | TanStack Router | Full type-safe params/search inference, file-based routes |
| Server state | TanStack Query | Caching, loading/error states, polling (ingest log) |
| UI state | `useState` / React context | Command palette open state lives in root — no extra library needed |
| Animations | Framer Motion | Spring physics, layout animations, shared element transitions |
| Styling | Tailwind CSS v4 | Utility-first, no runtime CSS-in-JS overhead |
| Testing | Vitest + React Testing Library + MSW | Integrated with Vite, fast, API mocking without backend |

### Aesthetic

**Light Clean** — inspired by Linear and Notion:
- Background: `slate-50` (`#f8fafc`)
- Cards: `white` with `slate-200` borders and subtle shadow
- Primary text: `slate-900`
- Accent: Indigo (`#6366f1`) for interactive elements and active states
- Typography: `Inter` variable font (system fallback), tight tracking on headings
- No gradients, no glassmorphism — clean surfaces only

### Navigation

**Top navigation bar** (persistent, root layout) with:
- Logo + wordmark left
- 5 nav links centre (Search, Graph, Documents, Upload, Settings)
- Active tab indicated by an animated indigo pill (`layoutId="nav-pill"` shared element)
- **⌘K Command Palette** button right — opens global overlay for search, navigation, and quick actions

---

## Architecture

### Directory layout

```
second-brain/
├── frontend/                        # New React SPA root
│   ├── src/
│   │   ├── routes/
│   │   │   ├── __root.tsx           # Root layout: TopNav + CommandPalette + <Outlet/>
│   │   │   ├── index.tsx            # / — Search & Q&A
│   │   │   ├── graph.tsx            # /graph — Cytoscape knowledge graph
│   │   │   ├── doc.$slug.tsx        # /doc/:slug — Document viewer
│   │   │   ├── upload.tsx           # /upload — File upload
│   │   │   └── settings.tsx         # /settings — LLM configuration
│   │   ├── components/
│   │   │   ├── TopNav.tsx
│   │   │   ├── CommandPalette.tsx
│   │   │   ├── AnswerCard.tsx
│   │   │   ├── SourceChip.tsx
│   │   │   ├── TagChip.tsx
│   │   │   └── DropZone.tsx
│   │   ├── api/
│   │   │   ├── useAsk.ts            # POST /query
│   │   │   ├── useGraphData.ts      # GET /graph/data
│   │   │   ├── useDoc.ts            # GET /doc/:slug (JSON variant)
│   │   │   ├── useSettings.ts       # GET + POST /settings
│   │   │   ├── useIngestLog.ts      # GET /ingest/log (polls every 5s)
│   │   │   └── useUpload.ts         # POST /upload
│   │   ├── lib/
│   │   │   └── motion.ts            # Shared Framer Motion variants
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── brain/                           # FastAPI — unchanged except additions below
│   └── server.py                   # + CORS middleware + /doc JSON variant + SPA catch-all
├── docs/
│   └── superpowers/specs/
│       └── 2026-04-29-frontend-redesign-design.md
└── docker-compose.yml               # + frontend build stage
```

### FastAPI changes (minimal)

1. **CORS middleware** — allow `http://localhost:5173` in development
2. **`GET /doc/{slug}` JSON variant** — if `Accept: application/json`, return `{slug, title, content_html, tags}` instead of rendered HTML template
3. **SPA catch-all** — `GET /{full_path:path}` serves `frontend/dist/index.html` for any non-API route in production
4. **Vite dev proxy** — `vite.config.ts` proxies `/api/*` → `http://localhost:8000` (stripping `/api` prefix); all frontend fetch calls use `/api/...`

No existing routes are modified or removed. Jinja2 templates are kept during transition, removed in the final phase.

---

## Pages

### `/` — Search & Q&A

- Large search input, centred, auto-focused on mount
- Submit triggers `useAsk` mutation → shows `AnswerCard` below with staggered text reveal
- `AnswerCard`: left indigo border, answer text, source chips at bottom linking to `/doc/:slug`
- Empty state: recent ingestion events from `useIngestLog` displayed as a document grid
- Animation: answer card slides up with spring, source chips stagger in

### `/graph` — Knowledge Graph

- Full-bleed layout (no padding), Cytoscape.js wrapped in a React ref
- Legend card overlaid bottom-left (wikilink = indigo, tag = amber, semantic = cyan)
- Clicking a node navigates to `/doc/:slug` via TanStack Router
- Empty state when no documents indexed
- Animation: fade-in on mount, node info tooltip animates in on hover

### `/doc/:slug` — Document Viewer

- Centred article layout, max-width 65ch for body
- Breadcrumb: `Search / Graph / <title>` — each segment links back
- Tags as coloured chips above body
- Wikilinks (`[[slug]]`) rendered as `<Link>` components → client-side navigation
- Animation: page slides in from right on navigate, back from left on browser-back

### `/upload` — File Upload

- Dashed drop zone with indigo border pulse animation when file is dragged over
- Accepted formats listed below zone
- Upload progress: animated progress bar with spring easing
- Success/error states with `AnimatePresence` transition
- Recent ingestion log below (polls via `useIngestLog`)

### `/settings` — LLM Configuration

- Same fields as current settings page, rebuilt in React
- Backend toggle (Anthropic / LocalAI) uses `AnimatePresence` to show/hide model fields
- Test connection button → inline result with colour-coded status
- Save button → optimistic update via TanStack Query mutation

---

## Animation System

All motion is defined in `src/lib/motion.ts` as reusable variants:

```typescript
export const pageVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
  exit:    { opacity: 0, x: -20 },
}

export const listVariants = {
  animate: { transition: { staggerChildren: 0.05 } },
}

export const itemVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 400, damping: 28 } },
}
```

Key animations:
- **Nav pill**: `layoutId="nav-pill"` shared element — pill slides between active links
- **Page transitions**: `AnimatePresence mode="wait"` on the router outlet
- **Answer reveal**: `staggerChildren` 50ms on answer paragraphs
- **Command palette**: spring `y: -16 → 0` + `opacity` on open, reversed on close
- **Drop zone**: `scale` pulse on drag-over (1 → 1.01 → 1, loop)
- **Upload progress**: `width` animated with spring

---

## Testing Strategy

**Framework:** Vitest + React Testing Library + MSW (Mock Service Worker)

Coverage targets:
- `TopNav`: renders all links, active link gets pill, ⌘K opens palette
- `CommandPalette`: opens on ⌘K, filters results as user types, keyboard navigation (↑↓ Enter Escape), closes on outside click
- `index` route: search input present, submitting calls mutation, answer card renders, sources link correctly
- `graph` route: Cytoscape wrapper mounts, empty state renders when data is empty
- `upload` route: drop zone accepts files, progress bar appears, success/error states
- `settings` route: form fields render with current config, save mutation fires on submit, backend toggle shows/hides fields
- API hooks: loading state, success state, error state for each hook

Python tests (`pytest`) are unchanged — they test the FastAPI layer independently.

---

## Build & Deployment

### Development

```bash
# Terminal 1
python -m brain.app           # FastAPI on :8000

# Terminal 2
cd frontend && npm run dev    # Vite on :5173 with proxy to :8000
```

### Production (Docker)

Multi-stage Dockerfile:

```dockerfile
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build            # → /app/frontend/dist

FROM python:3.11-slim
# ... (existing Python setup)
COPY --from=frontend-build /app/frontend/dist /app/static/dist
# FastAPI serves /app/static/dist as StaticFiles + SPA catch-all
```

`docker-compose.yml`: `brain` service build unchanged — the Dockerfile handles the frontend build internally.

---

## Migration Plan

| Phase | Scope | Backend changes |
|---|---|---|
| 1 | Scaffold `frontend/`, Vite config, TanStack setup, empty routes | Add CORS + `/doc` JSON variant |
| 2 | `__root.tsx` (TopNav + CommandPalette) + routing wired up | — |
| 3 | Implement all 5 pages with Framer Motion animations | — |
| 4 | Tests, Dockerfile update, SPA catch-all, remove Jinja2 templates | Add SPA catch-all |

---

## Consequences

**Positive:**
- Modern, maintainable frontend with type-safe routing
- Expressive animations impossible with vanilla JS
- Clear separation: React owns UI, FastAPI owns data
- Vitest runs fast without needing a browser or server

**Negative:**
- Node.js required in dev environment and Docker build
- Initial setup overhead (package.json, Vite config, TanStack config)
- Cytoscape.js needs a React wrapper (ref-based imperative API)
- ⌘K (Mac) / Ctrl+K (Windows/Linux) shortcut needs careful `preventDefault` to avoid browser conflicts
