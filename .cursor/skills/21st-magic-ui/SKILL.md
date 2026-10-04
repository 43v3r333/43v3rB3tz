---
name: 21st-magic-ui
description: Use 21st.dev Magic MCP for SaaS UI generation in this repo; align with Next.js and Tailwind conventions.
---

# 21st.dev Magic UI (ProphitBet SaaS)

Use when the user wants Magic MCP, `/ui` workflows, or 21st.dev–style components in the **SaaS frontend** (`prophitbet-saas/frontend/`).

## Setup

- MCP is **IDE-only** ([magic-mcp](https://github.com/21st-dev/magic-mcp)); configure Cursor with an API key per [docs/cursor-21st-magic.md](docs/cursor-21st-magic.md). Do not commit keys.
- Magic is **not** an npm dependency of the app.

## When generating or editing UI

1. Place new components under `prophitbet-saas/frontend/components/` or `app/` as appropriate for the App Router.
2. Reuse existing classes: `card`, `btn-primary`, `btn-secondary`, `input`, `brand-*` — see `prophitbet-saas/frontend/app/globals.css`.
3. Use `"use client"` when the component needs hooks or browser APIs; follow patterns in existing pages.
4. Call the backend via `lib/api.ts` and `NEXT_PUBLIC_API_URL`; do not fork ML logic into `prophitbet-saas/backend`.
5. Scoped rule: [saas-frontend.mdc](.cursor/rules/saas-frontend.mdc).

## Reference

- Full team doc: [docs/cursor-21st-magic.md](docs/cursor-21st-magic.md)
