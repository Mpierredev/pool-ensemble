from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import httpx
import yaml

DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
DDRAGON_CHAMPION_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"

TAG_TO_CLASS: dict[str, str] = {
    "Fighter": "bruiser",
    "Tank": "tank",
    "Mage": "mage",
    "Assassin": "assassin",
    "Marksman": "marksman",
    "Support": "enchanter",
}

TAG_TO_DAMAGE: dict[str, dict[str, float]] = {
    "Fighter": {"physical": 0.9, "magic": 0.1},
    "Tank": {"magic": 0.6, "physical": 0.4},
    "Mage": {"magic": 1.0},
    "Assassin": {"physical": 0.8, "magic": 0.2},
    "Marksman": {"physical": 0.9, "magic": 0.1},
    "Support": {"magic": 0.9, "physical": 0.1},
}

TAG_TO_ROLE: dict[str, dict[str, float]] = {
    "Fighter": {"top": 1.0},
    "Tank": {"top": 0.5, "support": 0.5},
    "Mage": {"mid": 1.0},
    "Assassin": {"mid": 0.6, "jungle": 0.4},
    "Marksman": {"bot": 1.0},
    "Support": {"support": 1.0},
}


def fetch_latest_version(client: httpx.Client) -> str:
    response = client.get(DDRAGON_VERSIONS_URL, timeout=15.0)
    response.raise_for_status()
    versions: list[str] = response.json()
    if not versions:
        raise RuntimeError("Empty Data Dragon version list")
    return versions[0]


def fetch_champions(client: httpx.Client, version: str) -> list[dict[str, Any]]:
    url = DDRAGON_CHAMPION_URL.format(version=version)
    response = client.get(url, timeout=20.0)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    data: dict[str, dict[str, Any]] = payload["data"]
    champions = list(data.values())
    champions.sort(key=lambda item: str(item["id"]))
    return champions


def build_starter_profile(raw: dict[str, Any]) -> dict[str, Any]:
    tags: list[str] = list(raw.get("tags", []))
    primary_tag = tags[0] if tags else "Fighter"
    secondary_tag = tags[1] if len(tags) > 1 else None

    classes: dict[str, float] = {TAG_TO_CLASS.get(primary_tag, "specialist"): 0.7}
    if secondary_tag is not None:
        sec_class = TAG_TO_CLASS.get(secondary_tag, "specialist")
        if sec_class not in classes:
            classes[sec_class] = 0.3
        else:
            classes[sec_class] = 1.0

    roles = dict(TAG_TO_ROLE.get(primary_tag, {"mid": 1.0}))
    damage = dict(TAG_TO_DAMAGE.get(primary_tag, {"physical": 0.5, "magic": 0.5}))
    info: dict[str, int] = raw.get("info", {})
    difficulty_raw = int(info.get("difficulty", 5))
    difficulty = round(min(1.0, max(0.1, difficulty_raw / 10.0)), 2)

    return {
        "id": str(raw["id"]),
        "champion_id": int(raw["key"]),
        "name": str(raw["name"]),
        "roles": roles,
        "classes": classes,
        "damage": damage,
        "style": {"skirmish": 0.5},
        "mobility": 0.5,
        "difficulty": difficulty,
        "off_meta": False,
        "tags": [tag.lower() for tag in tags],
        "needs_review": True,
    }


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    path.write_text(rendered, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync champion roster from Data Dragon into data/ddragon_manifest.yaml",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Path to the data directory",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Optional explicit Data Dragon patch version",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether all live champions exist and are marked reviewed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data_dir: Path = args.data_dir
    champions_dir = data_dir / "champions"
    champions_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as client:
        version = args.version or fetch_latest_version(client)
        raw_champions = fetch_champions(client, version)

    manifest_entries = [
        {
            "id": str(item["id"]),
            "champion_id": int(item["key"]),
            "name": str(item["name"]),
            "ddragon_tags": list(item.get("tags", [])),
        }
        for item in raw_champions
    ]

    if args.check:
        missing: list[str] = []
        unreviewed: list[str] = []
        for entry in manifest_entries:
            champ_id = str(entry["id"])
            profile_path = champions_dir / f"{champ_id.lower()}.yaml"
            if not profile_path.is_file():
                missing.append(champ_id)
                continue
            loaded = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict) or loaded.get("needs_review", False):
                unreviewed.append(champ_id)
        if missing or unreviewed:
            if missing:
                sys.stderr.write(f"Missing champion profiles: {', '.join(missing)}\n")
            if unreviewed:
                sys.stderr.write(f"Champions pending review: {', '.join(unreviewed)}\n")
            return 1
        sys.stdout.write(
            f"All {len(manifest_entries)} champions in Data Dragon {version} are reviewed.\n"
        )
        return 0

    write_yaml(
        data_dir / "ddragon_manifest.yaml",
        {"version": version, "champions": manifest_entries},
    )

    created_count = 0
    for item in raw_champions:
        champ_id = str(item["id"])
        profile_path = champions_dir / f"{champ_id.lower()}.yaml"
        if not profile_path.is_file():
            write_yaml(profile_path, build_starter_profile(item))
            created_count += 1

    sys.stdout.write(
        f"Synced {len(manifest_entries)} champions for patch {version}; "
        f"created {created_count} starter profile(s).\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
