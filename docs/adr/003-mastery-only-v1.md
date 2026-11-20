# ADR-003: Champion mastery only in v1

## Status

Accepted

## Context

Under a personal Riot API key (100 requests per 2 minutes), fetching recent match histories requires one API request per match. Analyzing 20 matches per user would exhaust the rate limit after just a few concurrent visitors.

## Decision

Build v1 pools exclusively from Account-v1 and Champion-Mastery-v4 (2 requests per uncached lookup), using `lastPlayTime` from the mastery response as the recency signal.

## Consequences

- Each uncached analysis consumes only 2 Riot API requests, allowing roughly 50 fresh lookups per 2-minute window.
- Match-level signals such as recent role changes or lane performance are deferred until production API key approval justifies a separate ADR.
