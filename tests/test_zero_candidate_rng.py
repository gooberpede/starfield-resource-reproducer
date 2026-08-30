from dataclasses import replace

import pytest

from starfield_resource_reproducer.diagnostics import EventKind
from starfield_resource_reproducer.domain import FormId, GenerationRarity, IRESNode
from starfield_resource_reproducer.generation import (
    ZeroCandidatePolicy,
    generate_family,
)
from starfield_resource_reproducer.prng import StarfieldRng


def _empty_family(generation_data, policy: ZeroCandidatePolicy):
    mimas = generation_data[FormId("0005DEC0")]
    source = next(
        entry
        for entry in mimas.biomes[0].effective_rsgd.entries
        if entry.resource_name == "Nickel"
    )
    root_id = FormId("FE000001")
    root = replace(
        source,
        resource_form_id=root_id,
        resource_editor_id="SyntheticRoot",
        resource_name="Synthetic Root",
        resource_rarity=GenerationRarity.COMMON,
    )
    graph = {
        root_id: IRESNode(
            root_id,
            "SyntheticRoot",
            "Synthetic Root",
            GenerationRarity.COMMON,
            (),
        )
    }
    rng = StarfieldRng(1)
    family = generate_family(
        root, graph, rng, zero_candidate_policy=policy
    )
    empty_events = tuple(
        item
        for item in family.events
        if item.kind is EventKind.DESCENDANT_OMITTED
        and item.get("reason") == "no_candidates"
    )
    return rng, family, empty_events


@pytest.mark.parametrize(
    ("policy", "draws_per_level", "operations"),
    [
        (
            ZeroCandidatePolicy.CONSUME_RAW,
            1,
            ("raw_advance_semantics_unknown",),
        ),
        (ZeroCandidatePolicy.CONSUME_NONE, 0, ()),
        (ZeroCandidatePolicy.CONSUME_INCLUSION, 1, ("inclusion",)),
        (
            ZeroCandidatePolicy.CONSUME_BOTH,
            2,
            ("inclusion", "index_raw_equivalent"),
        ),
    ],
)
def test_zero_candidate_policy_exposes_draw_count_and_operation_semantics(
    generation_data, policy, draws_per_level, operations
) -> None:
    rng, family, empty_events = _empty_family(generation_data, policy)

    assert rng.draw_count == 4 * draws_per_level
    assert len(empty_events) == 4
    assert all(level.selected_candidate is None for level in family.levels)
    assert all(item["raw_draws_consumed"] == draws_per_level for item in empty_events)
    assert all(item["operation_types"] == operations for item in empty_events)
    assert all(item["structural_node_changed"] is False for item in empty_events)
    expected_status = (
        "PROVEN"
        if policy is ZeroCandidatePolicy.CONSUME_RAW
        else "COUNTERFACTUAL / NOT RUNTIME-PROVEN"
    )
    assert all(item["evidence_status"] == expected_status for item in empty_events)


def test_production_raw_advance_does_not_claim_index_semantics(
    generation_data,
) -> None:
    _, _, empty_events = _empty_family(
        generation_data, ZeroCandidatePolicy.CONSUME_RAW
    )

    assert all(item["index_rng_consumed"] is False for item in empty_events)
    assert all(
        item["index_raw_equivalent_consumed"] is False for item in empty_events
    )
    assert all(item["inclusion_rng_consumed"] is False for item in empty_events)
    assert all(item["raw_values_consumed"] for item in empty_events)


def test_zero_candidate_policy_rejects_untyped_string(generation_data) -> None:
    with pytest.raises(TypeError, match="ZeroCandidatePolicy"):
        _empty_family(generation_data, "CONSUME_NONE")  # type: ignore[arg-type]
