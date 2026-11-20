# ADR-004: Ephemeral Redis storage with TTL

## Status

Accepted

## Context

Shareable results only need to remain accessible while links circulate, and aggregate archetype counts are lightweight counters. Managed free-tier relational databases either expire periodically or require paid plans.

## Decision

Store cached analysis results, share payloads, and aggregate archetype counters in Redis with explicit TTLs (12-24 hours for PUUID cache, 30 days for shared results), keeping command count minimal via pipelines.

## Consequences

- Free-tier serverless Redis (Upstash) covers persistence with zero idle expiration.
- Command budget per request remains predictable; keeping commands low avoids hitting the monthly free-tier cap.
- Long-term historical queries are out of scope unless a relational store is added later.
