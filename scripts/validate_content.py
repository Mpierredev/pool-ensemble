from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pool_ensemble.content import (
    Locale,
    load_content_bundle,
    load_copy_bank,
    load_manifest,
)
from pool_ensemble.domain.exceptions import InvalidContentError

MIN_ARCHETYPE_LINES = 8
MIN_TRAIT_LINES = 3
LOCALES: tuple[Locale, ...] = ("pt-BR", "en")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate champion, archetype, and copy YAML content",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Path to the data directory",
    )
    parser.add_argument(
        "--require-copy",
        action="store_true",
        help="Fail unless all archetypes and traits have complete copy in both locales",
    )
    return parser.parse_args(argv)


def validate_data(data_dir: Path, *, require_copy: bool = False) -> tuple[int, int]:
    manifest = load_manifest(data_dir / "ddragon_manifest.yaml")
    bundle = load_content_bundle(data_dir, require_complete=True)

    manifest_ids = {entry.id: entry for entry in manifest.champions}
    loaded_ids = set(bundle.champions.keys())

    missing = sorted(set(manifest_ids.keys()) - loaded_ids)
    if missing:
        raise InvalidContentError(f"Champions missing from data/champions: {', '.join(missing)}")

    extra = sorted(loaded_ids - set(manifest_ids.keys()))
    if extra:
        raise InvalidContentError(
            f"Champions not present in ddragon_manifest.yaml: {', '.join(extra)}"
        )

    for champ_id, entry in manifest_ids.items():
        profile = bundle.champions[champ_id]
        if profile.champion_id != entry.champion_id:
            raise InvalidContentError(
                f"Numeric id mismatch for {champ_id}: "
                f"manifest={entry.champion_id}, profile={profile.champion_id}"
            )

    for locale in LOCALES:
        copy_dir = data_dir / "copy" / locale
        if copy_dir.is_dir():
            bank = load_copy_bank(copy_dir, locale)
            if require_copy:
                for archetype in bundle.archetypes:
                    copy = bank.archetypes.get(archetype.id)
                    if copy is None:
                        raise InvalidContentError(
                            f"Missing {locale} copy for archetype '{archetype.id}'"
                        )
                    if len(copy.lines) < MIN_ARCHETYPE_LINES:
                        raise InvalidContentError(
                            f"Archetype '{archetype.id}' ({locale}) needs at least "
                            f"{MIN_ARCHETYPE_LINES} lines, found {len(copy.lines)}"
                        )
                for trait_id, trait_copy in bank.traits.items():
                    if len(trait_copy.lines) < MIN_TRAIT_LINES:
                        raise InvalidContentError(
                            f"Trait '{trait_id}' ({locale}) needs at least "
                            f"{MIN_TRAIT_LINES} lines, found {len(trait_copy.lines)}"
                        )

    return len(bundle.champions), len(bundle.archetypes)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        champ_count, archetype_count = validate_data(
            args.data_dir,
            require_copy=args.require_copy,
        )
    except InvalidContentError as exc:
        sys.stderr.write(f"Content validation failed: {exc}\n")
        return 1

    sys.stdout.write(
        f"Content validation passed: {champ_count} champions, {archetype_count} archetypes.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
