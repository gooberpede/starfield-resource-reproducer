"""Construct structural descendant candidates from the canonical IRES graph.

Purpose:
    Isolate the graph walk used by resource-family generation.
Responsibilities:
    Combine direct children of the family root and current structural node,
    preserve IRES order, de-duplicate by FormID, and filter by requested rarity.
Boundaries:
    This module does not consume RNG, evaluate inclusion, or emit resources.
Evidence notes:
    The root-plus-current scan and source ordering are PROVEN. Mimas L1 proves
    that scanning the root twice yields one structural Cobalt candidate, so
    duplicate FormIDs are removed while retaining their first occurrence.
"""

from collections.abc import Mapping

from .domain import FormId, GenerationRarity, IRESNode, ResourceRef


def build_descendant_candidates(
    root_form_id: FormId,
    current_form_id: FormId,
    rarity: GenerationRarity,
    ires_nodes: Mapping[FormId, IRESNode],
) -> tuple[ResourceRef, ...]:
    """Return ordered candidates from ``children(root) + children(current)``.

    Missing graph nodes are rejected rather than silently treated as leaves,
    because the canonical hierarchy is an authoritative static input.
    """

    try:
        root = ires_nodes[root_form_id]
        current = ires_nodes[current_form_id]
    except KeyError as error:
        missing = error.args[0]
        raise ValueError(f"IRES graph has no node for resource {missing}") from error

    candidates: list[ResourceRef] = []
    seen: set[FormId] = set()
    for child in (*root.children, *current.children):
        if child.form_id in seen:
            continue
        seen.add(child.form_id)
        if child.rarity is rarity:
            candidates.append(child)
    return tuple(candidates)
