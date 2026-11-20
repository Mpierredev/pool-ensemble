# ADR-006: Server-side PNG card rendering with Pillow

## Status

Accepted

## Context

Both user downloads and Open Graph previews require identical, crisp card images regardless of browser font availability, viewport size, or canvas quirks. Running a headless browser in the backend container would inflate memory usage beyond free-tier limits.

## Decision

Render PNG cards (1200x675 and 1080x1350) on the server with Pillow using locally packaged fonts and pre-fetched champion icons.

## Consequences

- Cards look identical across X previews and downloads without runtime network dependencies.
- Card images can be cached aggressively by result ID.
- Layout changes are verified deterministically with image snapshot hash tests.
