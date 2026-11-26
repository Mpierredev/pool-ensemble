# Classification algorithm

Pool Ensemble classifies champion pools deterministically using weighted mastery vectors, cosine similarity against YAML archetype vectors, explicit requirement penalties, and rule-based pool traits.

## 1. Weighted pool (`build_pool`)

Given champion mastery entries `(champion_id, points, last_play_time)` and an explicit `now` timestamp:

1. Discard entries with `points <= 0` or unknown `champion_id`, keeping the strongest entry if duplicates exist.
2. Compute raw weight per champion:

```text
raw_weight = ln(1 + points) * exp(-days_since / 180)
```

3. Sort descending by `raw_weight` (breaking ties by `champion_id`), keep at most the top 8 champions, normalize weights to sum to `1.0`, drop entries below `0.02` (always preserving at least the top champion), and re-normalize to `1.0`.

## 2. Feature vector (`extract_features`)

Every champion profile lives in a 30-dimensional vector space (`0.0` to `1.0`):

- `roles.*`: `top`, `jungle`, `mid`, `bot`, `support`
- `classes.*`: `enchanter`, `mage`, `assassin`, `diver`, `bruiser`, `marksman`, `tank`, `duelist`, `specialist`
- `damage.*`: `physical`, `magic`, `true`
- `style.*`: `burst`, `poke`, `control`, `pick`, `engage`, `dive`, `peel`, `skirmish`, `splitpush`, `scaling`, `chaos`
- `mobility`, `difficulty`

The player vector is the weighted sum of each champion's profile multiplied by its pool weight.

## 3. Archetype scoring (`classify_pool`)

- Pools with fewer than 3 champions immediately return `estreia_temporada` (`small_pool` fallback).
- For every regular archetype:
  - `cosine = dot(player, archetype) / (||player|| * ||archetype||)`
  - `signature_bonus = 0.12 * min(1.0, sum_of_signature_champion_weights)`
  - For each violated `requires` bound (`min` or `max`), add `0.25 + 0.60 * shortfall` to `penalty`.
  - `score = clamp(cosine + signature_bonus - penalty + score_bias, 0.0, 1.0)`
- If the top score is below `0.42`, return `elenco_caotico` (`chaotic` fallback).
- Otherwise, the highest score is `primary`. If the runner-up is at least `0.36` and within `0.25` of `primary`, it becomes `secondary`, and both percentages are normalized to sum to `100.0%`.

## 4. Worked numerical example

Suppose a pool at `now = 2026-11-20T12:00:00Z` has:

| Champion | Points | Days since played | `ln(1 + points)` | `exp(-d / 180)` | Raw weight | Normalized weight |
|---|---|---|---|---|---|---|
| Janna | 120,000 | 5 | 11.6953 | 0.9726 | 11.3749 | 0.377 |
| Lulu | 90,000 | 12 | 11.4076 | 0.9355 | 10.6719 | 0.353 |
| Orianna | 35,000 | 45 | 10.4631 | 0.7788 | 8.1487 | 0.270 |

For a pure enchanter pool (`Janna 0.40`, `Lulu 0.35`, `Soraka 0.25`):

- `roles.support = 1.0`, `classes.enchanter = 1.0`, `style.peel = 0.98`, `damage.magic = 0.945`, `mobility = 0.453`.
- Against `sitcom_suportes`, cosine similarity is above `0.97`, all `requires` checks (`classes.enchanter >= 0.35`, `style.peel >= 0.45`) pass with zero penalty, and signature bonus adds `0.12`, clamping the score to `1.0`.
- Against `reality_tanks`, `classes.tank` is `0.0 < 0.40` and `style.engage` is `0.0 < 0.45`, triggering requirement penalties that drop the score to `0.0`.

## 5. Pool traits (`detect_traits`)

Independent traits are evaluated on the weighted pool and feature vector:

- `one_trick`: top champion weight `>= 0.55`
- `wide_pool`: at least 6 champions with weight `>= 0.05`
- `off_meta`: combined weight of `off_meta: true` champions `>= 0.30`
- `all_roles`: every one of the 5 roles has weight `>= 0.08`
- `single_role`: not `all_roles`, and strongest role holds `>= 85%` of total role weight
- `low_mobility`: pool `mobility <= 0.30`
- `high_mobility`: pool `mobility >= 0.72`
