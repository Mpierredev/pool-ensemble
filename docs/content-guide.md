# Content guide

All champion profiles, archetype definitions, and localized copy lines live in `data/` as schema-validated YAML files. Adding or tuning content does not require changing Python code.

## Directory layout

```text
data/
  ddragon_manifest.yaml    Synced patch version and Data Dragon champion IDs
  champions/*.yaml         One YAML file per champion (<id.lower()>.yaml)
  archetypes/*.yaml        One YAML file per archetype (<id>.yaml)
  copy/{pt-BR,en}/*.yaml   Localized archetype and trait copy
```

## Champion schema (`data/champions/<id.lower()>.yaml`)

Allowed keys inside maps:

- `roles`: `top`, `jungle`, `mid`, `bot`, `support`
- `classes`: `enchanter`, `mage`, `assassin`, `diver`, `bruiser`, `marksman`, `tank`, `duelist`, `specialist`
- `damage`: `physical`, `magic`, `true`
- `style`: `burst`, `poke`, `control`, `pick`, `engage`, `dive`, `peel`, `skirmish`, `splitpush`, `scaling`, `chaos`

All map values, `mobility`, and `difficulty` must be floats between `0.0` and `1.0`.

Example (`data/champions/ahri.yaml`):

```yaml
id: Ahri
champion_id: 103
name: Ahri
roles:
  mid: 1.0
classes:
  mage: 0.7
  assassin: 0.3
damage:
  magic: 0.9
  true: 0.1
style:
  burst: 0.65
  pick: 0.7
  poke: 0.25
mobility: 0.75
difficulty: 0.5
off_meta: false
tags:
  - charm
  - fox
  - roam
needs_review: false
```

## Archetype schema (`data/archetypes/<id>.yaml`)

Example:

```yaml
id: terror_divers
weight_vector:
  classes:
    diver: 0.9
    bruiser: 0.3
  style:
    dive: 0.9
    engage: 0.8
    skirmish: 0.5
  mobility: 0.65
requires:
  - feature: style.dive
    min: 0.45
  - feature: classes.diver
    min: 0.25
signature_champions:
  - Vi
  - JarvanIV
  - Diana
rarity_hint: rare
palette:
  bg: "#120a14"
  accent: "#c0334d"
```

Every `signature_champions` entry must match a valid `id` in `data/champions/`.

## Copy schema (`data/copy/{pt-BR,en}/`)

Archetype copy (`<archetype_id>.yaml`):

```yaml
archetype_id: terror_divers
title: Terror de Divers
subtitle: A vitima nunca ve chegar
lines:
  - "Line 1"
roast_lines:
  - "Optional roast line"
```

Trait copy (`traits.yaml`):

```yaml
traits:
  - trait_id: one_trick
    label: Mono campeao
    lines:
      - "Line 1"
```

## Tooling scripts

Sync champion roster from Data Dragon (creates starter YAML with `needs_review: true` for new champions only):

```bash
cd apps/api && uv run python ../../scripts/sync_champions.py
```

Validate all YAML files offline (runs in CI):

```bash
make validate
```

Run the 5,000-pool balance simulation and verify all regular archetypes stay between 1.5% and 25.0%:

```bash
cd apps/api && uv run python ../../scripts/simulate_pools.py --count 5000 --seed 42 --strict
```
