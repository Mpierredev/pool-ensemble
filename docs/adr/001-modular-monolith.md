# ADR-001: Modular monolith backend

## Status

Accepted

## Context

Pool Ensemble has a narrow scope: fetch account mastery data, classify a champion pool deterministically, render a PNG card, and serve shareable links. Expected traffic does not warrant service-to-service network overhead, and infrastructure cost must remain zero.

## Decision

Build the backend as a single FastAPI service in `apps/api` organized into explicit domain, content, Riot client, storage, rendering, and sharing modules.

## Consequences

- Deployment fits within a single free-tier container.
- Module boundaries stay enforced in code and tests without distributed failure modes.
- Individual modules (such as card rendering) can be extracted later if load demands it.
