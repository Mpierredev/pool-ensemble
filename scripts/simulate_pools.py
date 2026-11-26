from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from pool_ensemble.content import ROLES, load_content_bundle
from pool_ensemble.domain import MasteryEntry, analyze_pool

if TYPE_CHECKING:
    from pool_ensemble.content import ChampionProfile, ContentBundle

FIXED_NOW = datetime(2026, 11, 20, 12, 0, 0, tzinfo=UTC)
MIN_REGULAR_PCT = 1.5
MAX_REGULAR_PCT = 25.0


def _weighted_sample_without_replacement(
    rng: random.Random,
    items: list[str],
    weights: list[float],
    count: int,
) -> list[str]:
    selected: list[str] = []
    pool_items = list(items)
    pool_weights = list(weights)
    for _ in range(min(count, len(pool_items))):
        total = sum(pool_weights)
        if total <= 0.0:
            pick_idx = rng.randrange(len(pool_items))
        else:
            threshold = rng.uniform(0.0, total)
            cumulative = 0.0
            pick_idx = len(pool_items) - 1
            for idx, weight in enumerate(pool_weights):
                cumulative += weight
                if cumulative >= threshold:
                    pick_idx = idx
                    break
        selected.append(pool_items.pop(pick_idx))
        pool_weights.pop(pick_idx)
    return selected


def _champion_score_for_focus(profile: ChampionProfile, focus_kind: str, focus_value: str) -> float:
    if focus_kind == "role":
        base = profile.roles.get(focus_value, 0.0)  # type: ignore[arg-type]
        return base + 0.015
    if focus_kind == "class":
        base = profile.classes.get(focus_value, 0.0)  # type: ignore[arg-type]
        return base + 0.01
    if focus_kind == "style":
        base = profile.style.get(focus_value, 0.0)  # type: ignore[arg-type]
        return base + 0.01
    return 1.0


def _generate_pool_entries(
    rng: random.Random,
    content: ContentBundle,
) -> list[MasteryEntry]:
    champion_ids = sorted(content.champions.keys())
    profiles = [content.champions[cid] for cid in champion_ids]

    bucket = rng.random()
    if bucket < 0.45:
        role = rng.choice(ROLES)
        weights = [_champion_score_for_focus(p, "role", role) for p in profiles]
        pool_size = rng.randint(4, 10)
        picked = _weighted_sample_without_replacement(rng, champion_ids, weights, pool_size)
    elif bucket < 0.78:
        focus_kind, focus_value = rng.choice(
            [
                ("class", "enchanter"),
                ("class", "mage"),
                ("class", "assassin"),
                ("class", "diver"),
                ("class", "marksman"),
                ("class", "tank"),
                ("class", "duelist"),
                ("class", "bruiser"),
                ("style", "splitpush"),
                ("style", "control"),
                ("style", "chaos"),
                ("style", "dive"),
            ]
        )
        weights = [_champion_score_for_focus(p, focus_kind, focus_value) for p in profiles]
        pool_size = rng.randint(4, 9)
        picked = _weighted_sample_without_replacement(rng, champion_ids, weights, pool_size)
    elif bucket < 0.91:
        role_a, role_b = rng.sample(ROLES, 2)
        weights = [
            0.6 * _champion_score_for_focus(p, "role", role_a)
            + 0.4 * _champion_score_for_focus(p, "role", role_b)
            for p in profiles
        ]
        pool_size = rng.randint(5, 10)
        picked = _weighted_sample_without_replacement(rng, champion_ids, weights, pool_size)
    elif bucket < 0.96:
        pool_size = rng.choice([1, 2, 3, 4])
        picked = rng.sample(champion_ids, pool_size)
    else:
        pool_size = rng.randint(5, 10)
        picked = rng.sample(champion_ids, pool_size)

    entries: list[MasteryEntry] = []
    base_points = rng.randint(25_000, 350_000)
    for rank, champ_id in enumerate(picked):
        decay_factor = (rank + 1) ** -1.25
        jitter = rng.uniform(0.65, 1.35)
        points = max(1_200, int(base_points * decay_factor * jitter))
        days_ago = rng.uniform(0.0, 180.0 if rank < 4 else 320.0)
        entries.append(
            MasteryEntry(
                champion_id=champ_id,
                points=points,
                last_play_time=FIXED_NOW - timedelta(days=days_ago),
            )
        )
    return entries


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate synthetic champion pools and report archetype balance",
    )
    parser.add_argument("--count", type=int, default=5000, help="Number of pools to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Path to the data directory",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any regular archetype falls outside 1.5%..25.0%",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    content = load_content_bundle(args.data_dir, require_complete=True)
    rng = random.Random(args.seed)

    primary_counts: Counter[str] = Counter()
    secondary_counts: Counter[str] = Counter()
    trait_counts: Counter[str] = Counter()

    for _ in range(args.count):
        entries = _generate_pool_entries(rng, content)
        analysis = analyze_pool(entries, content, FIXED_NOW)
        primary_counts[analysis.classification.primary.archetype_id] += 1
        if analysis.classification.secondary is not None:
            secondary_counts[analysis.classification.secondary.archetype_id] += 1
        for trait in analysis.traits:
            trait_counts[trait] += 1

    sys.stdout.write(f"Simulated {args.count} pools (seed={args.seed})\n\n")
    sys.stdout.write("Primary archetype distribution:\n")
    out_of_bounds: list[str] = []
    for archetype in sorted(content.archetypes, key=lambda item: -primary_counts[item.id]):
        count = primary_counts[archetype.id]
        pct = 100.0 * count / args.count
        tag = f"[{archetype.fallback_kind}]" if archetype.fallback_kind != "none" else ""
        sys.stdout.write(f"  {archetype.id:<24} {count:5d} ({pct:5.2f}%) {tag}\n")
        if archetype.fallback_kind == "none" and not (MIN_REGULAR_PCT <= pct <= MAX_REGULAR_PCT):
            out_of_bounds.append(f"{archetype.id}={pct:.2f}%")

    sys.stdout.write("\nTrait frequencies:\n")
    for trait_id, count in trait_counts.most_common():
        pct = 100.0 * count / args.count
        sys.stdout.write(f"  {trait_id:<24} {count:5d} ({pct:5.2f}%)\n")

    with_secondary = sum(secondary_counts.values())
    sys.stdout.write(
        f"\nPools with secondary archetype: {with_secondary} "
        f"({100.0 * with_secondary / args.count:.2f}%)\n"
    )

    if args.strict and out_of_bounds:
        sys.stderr.write(
            f"\nBalance check failed ({MIN_REGULAR_PCT}%..{MAX_REGULAR_PCT}%): "
            f"{', '.join(out_of_bounds)}\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
