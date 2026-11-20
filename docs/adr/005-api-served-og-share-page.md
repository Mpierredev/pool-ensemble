# ADR-005: API-served Open Graph share page

## Status

Accepted

## Context

Social crawlers (such as X) read Open Graph and Twitter Card metadata from the initial HTML response without executing client-side JavaScript. Hosting the frontend as a pure static SPA would prevent dynamic link previews for `/p/{id}` URLs without full SSR infrastructure.

## Decision

Serve `/p/{id}` directly from FastAPI as a minimal HTML document containing Open Graph and Twitter Card meta tags and redirecting human browsers to the SPA result route.

## Consequences

- Social platforms render accurate card previews with zero SSR complexity in `apps/web`.
- The frontend stays a simple static bundle deployable to Cloudflare Pages.
