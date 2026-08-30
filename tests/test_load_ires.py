import csv
from pathlib import Path

import pytest

from conftest import DATA_DIR
from starfield_resource_reproducer.domain import FormId, GenerationRarity
from starfield_resource_reproducer.load_data import DataValidationError, load_ires_hierarchy


def _node_named(ires_nodes, name: str):
    return next(node for node in ires_nodes.values() if node.name == name)


@pytest.mark.parametrize(
    ("parent", "expected"),
    [
        (
            "Nickel",
            [("Cobalt", GenerationRarity.UNCOMMON), ("Palladium", GenerationRarity.EXOTIC)],
        ),
        (
            "Uranium",
            [
                ("Iridium", GenerationRarity.UNCOMMON),
                ("Vanadium", GenerationRarity.RARE),
                ("Plutonium", GenerationRarity.EXOTIC),
            ],
        ),
        (
            "Copper",
            [("Fluorine", GenerationRarity.UNCOMMON), ("Gold", GenerationRarity.RARE)],
        ),
    ],
)
def test_ires_direct_edges(ires_nodes, parent: str, expected) -> None:
    node = _node_named(ires_nodes, parent)

    assert [(child.name, child.rarity) for child in node.children] == expected


def test_ires_leaf_has_no_fake_child(ires_nodes) -> None:
    assert _node_named(ires_nodes, "Beryllium").children == ()


def test_ires_integrity_counts(ires_nodes) -> None:
    with (DATA_DIR / "Starfield_IRES_Hierarchy.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        assert sum(1 for _ in csv.DictReader(source)) == 56

    assert len(ires_nodes) == 47
    assert sum(len(node.children) for node in ires_nodes.values()) == 35


def test_ires_reconciles_child_and_parent_identity(ires_nodes) -> None:
    nickel = _node_named(ires_nodes, "Nickel")
    cobalt_child = nickel.children[0]
    cobalt_node = ires_nodes[cobalt_child.form_id]

    assert cobalt_child.form_id == FormId("000057CE")
    assert (cobalt_child.editor_id, cobalt_child.name, cobalt_child.rarity) == (
        cobalt_node.editor_id,
        cobalt_node.name,
        cobalt_node.rarity,
    )


def test_ires_rejects_half_populated_child(tmp_path: Path) -> None:
    path = tmp_path / "ires.csv"
    with (DATA_DIR / "Starfield_IRES_Hierarchy.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        row = next(csv.DictReader(source))
    row["ChildEditorID"] = ""
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(DataValidationError, match="partially populated"):
        load_ires_hierarchy(path)
