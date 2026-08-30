from starfield_resource_reproducer.candidates import build_descendant_candidates
from starfield_resource_reproducer.domain import FormId, GenerationRarity


def _node_named(ires_nodes, name: str):
    return next(node for node in ires_nodes.values() if node.name == name)


def test_nickel_candidates_revisit_root_at_later_rarities(ires_nodes) -> None:
    nickel = _node_named(ires_nodes, "Nickel")
    cobalt = _node_named(ires_nodes, "Cobalt")
    platinum = _node_named(ires_nodes, "Platinum")

    uncommon = build_descendant_candidates(
        nickel.form_id, nickel.form_id, GenerationRarity.UNCOMMON, ires_nodes
    )
    rare = build_descendant_candidates(
        nickel.form_id, cobalt.form_id, GenerationRarity.RARE, ires_nodes
    )
    exotic = build_descendant_candidates(
        nickel.form_id, platinum.form_id, GenerationRarity.EXOTIC, ires_nodes
    )

    # Scanning the root twice at L1 must not duplicate Cobalt.
    assert [candidate.name for candidate in uncommon] == ["Cobalt"]
    assert [candidate.name for candidate in rare] == ["Platinum"]
    assert [candidate.name for candidate in exotic] == ["Palladium"]


def test_copper_rare_candidates_combine_root_and_current_branches(ires_nodes) -> None:
    copper = _node_named(ires_nodes, "Copper")
    fluorine = _node_named(ires_nodes, "Fluorine")

    candidates = build_descendant_candidates(
        copper.form_id, fluorine.form_id, GenerationRarity.RARE, ires_nodes
    )

    assert [candidate.name for candidate in candidates] == [
        "Gold",
        "Tetrafluorides",
    ]
    assert [candidate.form_id for candidate in candidates] == [
        FormId("000057D2"),
        FormId("000057D1"),
    ]
