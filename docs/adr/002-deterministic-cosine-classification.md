# ADR-002: Deterministic cosine classification with rules

## Status

Accepted

## Context

There is no labeled dataset of champion pool archetypes, and players expect consistent, explainable results when re-analyzing the same pool. Training and serving a supervised ML classifier would add opaque decisions and extra dependencies (`scikit-learn`) to the runtime image.

## Decision

Represent both player pools and archetypes as vectors in a shared feature space (roles, classes, damage profile, playstyle, mobility, difficulty). Rank archetypes using cosine similarity adjusted by signature-champion bonuses and explicit `requires` feature thresholds.

## Consequences

- Identical pools always yield identical primary and secondary archetypes.
- Community contributors can tune or add archetypes in YAML without training pipelines.
- Runtime math requires only NumPy, keeping the container small and cold starts fast.
