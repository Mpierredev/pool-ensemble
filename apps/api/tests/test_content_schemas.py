from __future__ import annotations

import pytest
from pydantic import ValidationError

from pool_ensemble.content.schemas import (
    FEATURE_KEYS,
    ArchetypeCopy,
    ArchetypeDefinition,
    ArchetypePalette,
    ChampionProfile,
    CopyBank,
    FeatureRequirement,
    TraitCopy,
    WeightVector,
)


def test_feature_keys_count_and_uniqueness() -> None:
    assert len(FEATURE_KEYS) == 30
    assert len(set(FEATURE_KEYS)) == 30


def test_champion_profile_completeness() -> None:
    complete = ChampionProfile(
        id="Ahri",
        champion_id=103,
        name="Ahri",
        roles={"mid": 1.0},
        classes={"mage": 0.7, "assassin": 0.3},
        damage={"magic": 1.0},
        style={"burst": 0.65, "pick": 0.7},
        mobility=0.75,
        difficulty=0.5,
    )
    assert complete.is_complete is True

    needs_review = complete.model_copy(update={"needs_review": True})
    assert needs_review.is_complete is False

    missing_style = ChampionProfile(
        id="Ahri",
        champion_id=103,
        name="Ahri",
        roles={"mid": 1.0},
        classes={"mage": 1.0},
        damage={"magic": 1.0},
        style={},
        mobility=0.75,
        difficulty=0.5,
    )
    assert missing_style.is_complete is False


def test_champion_profile_rejects_out_of_range_weight() -> None:
    with pytest.raises(ValidationError):
        ChampionProfile(
            id="Ahri",
            champion_id=103,
            name="Ahri",
            roles={"mid": 1.2},
            classes={"mage": 1.0},
            damage={"magic": 1.0},
            style={"burst": 0.5},
            mobility=0.5,
            difficulty=0.5,
        )


def test_feature_requirement_validation() -> None:
    req = FeatureRequirement(feature="style.dive", min=0.35, max=0.9)
    assert req.min == 0.35

    with pytest.raises(ValidationError):
        FeatureRequirement(feature="style.nonexistent", min=0.2)

    with pytest.raises(ValidationError):
        FeatureRequirement(feature="style.dive")

    with pytest.raises(ValidationError):
        FeatureRequirement(feature="style.dive", min=0.8, max=0.2)


def test_archetype_definition_and_palette_validation() -> None:
    archetype = ArchetypeDefinition(
        id="terror_divers",
        weight_vector=WeightVector(
            classes={"diver": 0.8},
            style={"dive": 0.9},
        ),
        signature_champions=("Vi",),
        palette=ArchetypePalette(bg="#120a14", accent="#c0334d"),
    )
    assert archetype.weight_vector.to_flat_dict() == {
        "classes.diver": 0.8,
        "style.dive": 0.9,
    }

    with pytest.raises(ValidationError):
        ArchetypePalette(bg="120a14", accent="#c0334d")

    with pytest.raises(ValidationError):
        ArchetypeDefinition(
            id="empty_regular",
            weight_vector=WeightVector(),
            signature_champions=("Vi",),
            palette=ArchetypePalette(bg="#120a14", accent="#c0334d"),
        )

    with pytest.raises(ValidationError):
        ArchetypeDefinition(
            id="no_signature",
            weight_vector=WeightVector(style={"dive": 0.5}),
            signature_champions=(),
            palette=ArchetypePalette(bg="#120a14", accent="#c0334d"),
        )


def test_copy_schemas_reject_blank_lines() -> None:
    copy = ArchetypeCopy(
        archetype_id="sitcom_suportes",
        title="Sitcom de Suportes",
        subtitle="Todo mundo se ajuda",
        lines=("Linha valida",),
        roast_lines=("Roast valido",),
    )
    trait_copy = TraitCopy(
        trait_id="one_trick",
        label="One trick",
        lines=("Um campeao apenas.",),
    )
    bank = CopyBank(
        locale="pt-BR",
        archetypes={copy.archetype_id: copy},
        traits={trait_copy.trait_id: trait_copy},
    )
    assert bank.locale == "pt-BR"

    with pytest.raises(ValidationError):
        ArchetypeCopy(
            archetype_id="sitcom_suportes",
            title="Sitcom",
            subtitle="Sub",
            lines=("   ",),
        )

    with pytest.raises(ValidationError):
        TraitCopy(trait_id="one_trick", label="One trick", lines=("",))
