---
name: gsap
description: Use GSAP (GreenSock Animation Platform) in this repo for performant UI motion — install patterns, Next.js App Router, and performance.
---

# GSAP in ProphitBet

Use when adding or changing animations in the SaaS frontend (`prophitbet-saas/frontend/`) or when optimizing animation bundle size.

## References

- Repository: [greensock/GSAP on GitHub](https://github.com/greensock/gsap)
- Docs and install: [gsap.com](https://gsap.com/docs/v3/)

## Runtime in this repo

GSAP is loaded from **`public/vendor/gsap.min.js`** (UMD) via [`lib/loadGsap.ts`](prophitbet-saas/frontend/lib/loadGsap.ts) so Webpack does **not** `import "gsap"` from `node_modules`. That avoids `Can't resolve 'gsap'` when Docker or CI has an empty/stale `node_modules`.

Optional local types: install `gsap` as a devDependency only if you want IDE typings; runtime still uses the vendor file.

## Install (generic / plugins)

```bash
cd prophitbet-saas/frontend
# Only if using npm-imported GSAP elsewhere:
npm install gsap @gsap/react
```

- **Core**: `import gsap from "gsap"` — tree-shakeable; avoid importing from `gsap/all` unless many plugins are needed.
- **Plugins** (register once): `import { ScrollTrigger } from "gsap/ScrollTrigger"` then `gsap.registerPlugin(ScrollTrigger)`.

## Next.js App Router — performance rules

1. **Lazy-load GSAP** on the client so the first paint is not blocked by the animation chunk: `import("gsap")` inside `useLayoutEffect` or a dynamically imported client island.
2. **Prefer `@gsap/react` `useGSAP`** when the callback can run synchronously with `gsap` already loaded; pair with `scope` / refs for selector scoping and automatic cleanup.
3. **Use `gsap.context()`** (or `useGSAP` cleanup) so tweens revert on unmount — avoids leaks and orphaned DOM transforms.
4. **Respect `prefers-reduced-motion`**: skip motion or set `duration: 0` / instant setters when the user requests reduced motion (see `lib/motion.ts`).
5. **Avoid ScrollTrigger on every page** unless needed — it adds weight; lazy-register only on routes that use scroll-driven animation.
6. **Do not CDN-load GSAP in `layout.tsx`** for the whole app — that hurts caching and splits poorly; NPM + dynamic import is preferred for this codebase.

## Project helpers

- `lib/motion.ts` — `prefersReducedMotion()` for accessible fallbacks.

## Snippet: stagger + context cleanup

```tsx
useLayoutEffect(() => {
  let ctx: import("gsap").Context | undefined;
  const cancelled = { current: false };
  import("gsap").then(({ default: gsap }) => {
    if (cancelled.current || prefersReducedMotion()) return;
    ctx = gsap.context(() => {
      gsap.from(".card", { opacity: 0, y: 16, duration: 0.45, stagger: 0.06, ease: "power2.out" });
    }, containerRef);
  });
  return () => {
    cancelled.current = true;
    ctx?.revert();
  };
}, []);
```
