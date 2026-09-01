from pathlib import Path

from starfield_resource_reproducer.dossier import (
    build_planet_dossier,
    family_configuration_cutoffs,
    visible_insertion_cutoffs,
    write_dossier_events_csv,
)
from starfield_resource_reproducer.domain import FormId
from starfield_resource_reproducer.generation import generate_planet


FERMI_VII_A = FormId("0005DE3A")
MAAL_VIII = FormId("0005DE6F")
FERMI_III = FormId("0005DE2D")


def _dossier(planet_id, generation_data, ires_nodes, canonical_oracle):
    generation = generate_planet(generation_data[planet_id], ires_nodes)
    return build_planet_dossier(
        generation, canonical_oracle[planet_id], ires_nodes
    )


def test_event_and_family_ledgers_are_deterministic(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    first = _dossier(FERMI_VII_A, generation_data, ires_nodes, canonical_oracle)
    second = _dossier(FERMI_VII_A, generation_data, ires_nodes, canonical_oracle)

    assert first == second
    assert [item.root.name for item in first.families] == [
        "Uranium", "Nickel", "Copper"
    ]
    assert [item.cache_hit for item in first.families] == [False, False, False]
    assert [item.generated_family_count_after for item in first.families] == [1, 2, 3]


def test_resource_insertion_count_is_monotonic_and_first_divergence_is_stable(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    expected = {
        FERMI_VII_A: None,
        MAAL_VIII: ("Alkanes", 8),
        FERMI_III: None,
    }
    for planet_id, divergence in expected.items():
        dossier = _dossier(planet_id, generation_data, ires_nodes, canonical_oracle)
        assert [item.count_after for item in dossier.insertions] == list(
            range(1, len(dossier.insertions) + 1)
        )
        if divergence is None:
            assert dossier.first_divergence is None
        else:
            assert dossier.first_divergence is not None
            assert (
                dossier.first_divergence.resource.name,
                dossier.first_divergence.sequence,
            ) == divergence
            assert dossier.first_divergence.source_event == "RESOURCE_SLOT_OCCUPIED"


def test_canonical_annotation_and_counterfactuals_do_not_mutate_generation(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    generation = generate_planet(generation_data[MAAL_VIII], ires_nodes)
    predicted_before = generation.predicted_form_ids
    events_before = generation.events
    dossier = build_planet_dossier(
        generation, canonical_oracle[MAAL_VIII], ires_nodes
    )

    visible = visible_insertion_cutoffs(dossier, (5, 6, 7, 8))
    families = family_configuration_cutoffs(dossier, (4, 5))

    assert generation.predicted_form_ids == predicted_before
    assert generation.events == events_before
    assert visible[2].assessment == "COMPATIBLE WITH THIS CASE"
    assert visible[3].assessment == "INCOMPATIBLE WITH THIS CASE"
    assert all(item.assessment == "INCOMPATIBLE WITH THIS CASE" for item in families)


def test_csv_output_is_deterministic(
    generation_data, ires_nodes, canonical_oracle, tmp_path: Path
) -> None:
    dossiers = tuple(
        _dossier(planet_id, generation_data, ires_nodes, canonical_oracle)
        for planet_id in (FERMI_VII_A, MAAL_VIII, FERMI_III)
    )
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    write_dossier_events_csv(dossiers, first)
    write_dossier_events_csv(dossiers, second)

    assert first.read_bytes() == second.read_bytes()
    text = first.read_text(encoding="utf-8")
    assert text.startswith("PlanetFormID,PlanetName,EventIndex,RawDrawNumber")
    assert "Fluorine" in text
    assert "Alkanes" in text
    assert "Nickel" in text


def test_dossier_event_added_without_worked_case_generation_change(
    generation_data, ires_nodes
) -> None:
    decaran = generate_planet(generation_data[FormId("0005DF7F")], ires_nodes)

    assert decaran.final_draw_count == 10
    assert {resource.name for resource in decaran.predicted_resources} == {
        "Helium-3", "Uranium", "Iridium", "Vytinium"
    }
