from dataclasses import replace

from starfield_resource_reproducer.domain import FormId, ProjectData
from starfield_resource_reproducer.generation import generate_planet
from starfield_resource_reproducer.validation import (
    MatchStatus,
    MismatchSignature,
    compare_to_oracle,
    mismatch_csv_row,
    validate_all_planets,
    write_mismatch_csv,
)


MIMAS = FormId("0005DEC0")
OBERON = FormId("0005DECC")
KREET = FormId("0003F59F")
COBALT = FormId("000057CE")
PALLADIUM = FormId("000057CD")


def _comparison(generation_data, ires_nodes, canonical_oracle, expected):
    generation = generate_planet(generation_data[MIMAS], ires_nodes)
    canonical = replace(canonical_oracle[MIMAS], inorganic_resources=frozenset(expected))
    return compare_to_oracle(generation, canonical, ires_nodes)


def test_exact_and_high_level_set_statuses(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    actual = canonical_oracle[MIMAS].inorganic_resources

    exact = _comparison(generation_data, ires_nodes, canonical_oracle, actual)
    missing = _comparison(
        generation_data, ires_nodes, canonical_oracle, actual | {COBALT}
    )
    unexpected = _comparison(
        generation_data, ires_nodes, canonical_oracle, actual - {PALLADIUM}
    )
    mixed = _comparison(
        generation_data,
        ires_nodes,
        canonical_oracle,
        (actual - {PALLADIUM}) | {COBALT},
    )

    assert exact.match_status is MatchStatus.EXACT
    assert exact.mismatch_signature is MismatchSignature.EXACT
    assert missing.match_status is MatchStatus.MISSING_ONLY
    assert missing.missing_form_ids == frozenset({COBALT})
    assert unexpected.match_status is MatchStatus.UNEXPECTED_ONLY
    assert unexpected.unexpected_form_ids == frozenset({PALLADIUM})
    assert mixed.match_status is MatchStatus.MISSING_AND_UNEXPECTED
    assert mixed.mismatch_signature is MismatchSignature.SAME_FAMILY_SUBSTITUTION
    assert mixed.family_analysis.missing_family_roots == (FormId("000057CB"),)
    assert mixed.family_analysis.unexpected_family_roots == (FormId("000057CB"),)


def test_population_coverage_and_generation_errors_continue(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    project = ProjectData(
        planets={MIMAS: generation_data[MIMAS], OBERON: generation_data[OBERON]},
        ires_nodes=ires_nodes,
        oracle={MIMAS: canonical_oracle[MIMAS], KREET: canonical_oracle[KREET]},
    )

    def failing_generator(planet, graph):
        raise RuntimeError(f"synthetic failure for {planet.form_id}")

    result = validate_all_planets(project, generator=failing_generator)

    assert result.generation_planet_count == 2
    assert result.oracle_inorganic_planet_count == 2
    assert result.intersection_count == 1
    assert result.generation_only[0].planet_form_id == OBERON
    assert result.generation_only[0].signature is MismatchSignature.GENERATION_ONLY
    assert result.oracle_only[0].planet_form_id == KREET
    assert result.oracle_only[0].signature is MismatchSignature.ORACLE_ONLY
    assert result.planet_results[0].match_status is MatchStatus.GENERATION_ERROR
    assert result.planet_results[0].generation_error_type == "RuntimeError"
    assert result.aggregates.generation_errors == 1


def test_stable_result_and_csv_ordering(
    generation_data, ires_nodes, canonical_oracle, tmp_path
) -> None:
    project = ProjectData(
        planets={OBERON: generation_data[OBERON], MIMAS: generation_data[MIMAS]},
        ires_nodes=ires_nodes,
        oracle={OBERON: canonical_oracle[OBERON], MIMAS: canonical_oracle[MIMAS]},
    )
    first = validate_all_planets(project)
    second = validate_all_planets(project)

    assert first == second
    assert [item.planet_form_id for item in first.planet_results] == [MIMAS, OBERON]
    assert first.aggregates.exact_matches == 2
    assert first.aggregates.mismatches == 0

    row = mismatch_csv_row(first.planet_results[0])
    assert row["PredictedFormIDs"] == ";".join(
        str(item) for item in sorted(first.planet_results[0].predicted_form_ids)
    )
    output = tmp_path / "nested" / "mismatches.csv"
    write_mismatch_csv(first, output)
    assert output.read_text(encoding="utf-8").splitlines() == [
        ",".join(row.keys())
    ]


def test_complete_corpus_baseline_is_deterministic_and_consistent(
    generation_data, ires_nodes, canonical_oracle
) -> None:
    project = ProjectData(generation_data, ires_nodes, canonical_oracle)
    first = validate_all_planets(project)
    second = validate_all_planets(project)

    assert first == second
    assert first.generation_planet_count == 1444
    assert first.oracle_inorganic_planet_count == 1444
    assert first.intersection_count == 1444
    assert first.generation_only == ()
    assert first.oracle_only == ()
    assert len(first.planet_results) == first.intersection_count
    assert len({item.planet_form_id for item in first.planet_results}) == 1444
    assert first.aggregates.exact_matches == 1281
    assert first.aggregates.mismatches == 163
    assert first.aggregates.generation_errors == 0
    assert (
        first.aggregates.exact_matches + first.aggregates.mismatches
        == first.aggregates.total_validation_planets
    )
    assert sum(count for _, count in first.aggregates.mismatch_status_counts) == 163
