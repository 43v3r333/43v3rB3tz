# 21st.dev Magic MCP (Cursor / VS Code)

[21st-dev/magic-mcp](https://github.com/21st-dev/magic-mcp) is a **Model Context Protocol** server that connects your IDE to [21st.dev Magic](https://21st.dev/magic): AI-assisted UI generation from natural language (e.g. `/ui create a responsive stats card`). It is **not** an npm package bundled into the Next.js app—configuration lives in your IDE.

## Prerequisites

- **Node.js** (LTS recommended)
- A **Magic API key** from [21st.dev Magic Console](https://21st.dev/magic/console)
- **Cursor**, **Windsurf**, **VS Code**, or **Cline** (see upstream README for supported clients)

**Security:** Never commit API keys. Prefer **user-level** Cursor config (`~/.cursor/mcp.json` on macOS/Linux, `%USERPROFILE%\.cursor\mcp.json` on Windows) so secrets stay outside the repo.

## Recommended install (CLI)

From any directory:

```bash
npx @21st-dev/cli@latest install cursor --api-key <your-api-key>
```

Supported clients (upstream): `cursor`, `windsurf`, `cline`, `claude`.

## Manual Cursor configuration

1. Open or create your **user** MCP config file:
   - **Windows:** `%USERPROFILE%\.cursor\mcp.json`
   - **macOS / Linux:** `~/.cursor/mcp.json`
2. Merge the structure from [`mcp-21st-magic.example.json`](mcp-21st-magic.example.json) in this repo, replacing the API key placeholder with your key (or paste the JSON from the [magic-mcp README](https://github.com/21st-dev/magic-mcp) and adapt the `args` line).
3. Restart Cursor so the MCP server loads.

## VS Code (optional)

Upstream documents **VS Code** setup via User Settings JSON or workspace `.vscode/mcp.json` with `inputs` for the API key. See the [Installation section](https://github.com/21st-dev/magic-mcp#installation) in the magic-mcp README (“Method 3: VS Code Installation”).

## Using Magic in the agent

- In chat, use **`/ui`** and describe the component (e.g. `/ui create a modern navigation bar with responsive design`).
- Generated files are written into your project; review and adjust like any other code.

## ProphitBet conventions (SaaS frontend)

When generating UI for this repo’s SaaS:

| Topic | Guidance |
|--------|----------|
| **Location** | Prefer [`prophitbet-saas/frontend/components/`](../prophitbet-saas/frontend/components/) or [`prophitbet-saas/frontend/app/`](../prophitbet-saas/frontend/app/) under the App Router. |
| **Styling** | Use existing Tailwind patterns: `card`, `btn-primary`, `btn-secondary`, `input`, `brand-*` colors—see [`prophitbet-saas/frontend/app/globals.css`](../prophitbet-saas/frontend/app/globals.css). |
| **Client components** | Add `"use client"` when using hooks or browser-only APIs; match patterns in existing pages. |
| **API** | Use [`prophitbet-saas/frontend/lib/api.ts`](../prophitbet-saas/frontend/lib/api.ts) and env-based `NEXT_PUBLIC_API_URL`. |
| **Rules** | Follow [`.cursor/rules/saas-frontend.mdc`](../.cursor/rules/saas-frontend.mdc). |
| **Backend** | Do not duplicate ML or training logic in `prophitbet-saas/backend`; keep thin API adapters only. |

## References

- [21st-dev/magic-mcp on GitHub](https://github.com/21st-dev/magic-mcp)
- [21st.dev Magic](https://21st.dev/magic)
- Example MCP JSON (no secrets): [`mcp-21st-magic.example.json`](mcp-21st-magic.example.json)

## Git hygiene

If you create a **project-local** `.cursor/mcp.json` containing real keys, add that path to `.gitignore` or avoid committing it. Prefer user-level `~/.cursor/mcp.json` for team safety.
