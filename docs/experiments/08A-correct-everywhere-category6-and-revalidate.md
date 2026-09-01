# Brief 08A Category-6 Correction and Revalidation

## Scope and evidence

This run applies the Fermi VIII-b live-trace correction to the observed Creation
Kit Galaxy View Apply path. `FUN_141548920` scans each effective RSGD's ordinary
resource-entry array in authored order and emits entries whose referenced IRES
category is 6 / Everywhere. It does not consult DNAM Everywhere chance, substitute
Common chance, or consume RNG. Existing shared capacity, duplicate/provenance,
and pre-main ordering behavior is unchanged.

**COUNTERFACTUAL / FALSIFIED:** a one-entry effective RSGD is not generically
auto-selected. Kreet's one-entry Common RSGDs still use the normal category-0
weighted selector and consume the normal RNG draw.

## Full-corpus comparison

```text
                         07B baseline   Post-08A
population                      1,444       1,444
exact                           1,426       1,441
mismatches                         18           3
exact rate                     98.75%      99.79%
generation errors                  0           0
coverage-only bodies               0           0
```

Post-08A mismatch directions:

```text
prediction-only              3
oracle-only                  0
both-sides                   0
missing occurrences          0
unexpected occurrences       3
```

All 15 `OceanDefaultRes` Water-only residuals in the 07B report disappeared.
The regenerated machine-readable report is
`validation/full-canonical-mismatches.csv`.

## Exact residuals

| Planet | FormID | Signature | Residual |
| --- | --- | --- | --- |
| Zeta Ophiuchi I | `0005E151` | `UNEXPECTED_ROOT` | unexpected Chlorine `000057D5`; atmospheric/Common collision |
| Indum IV-d | `0005E19A` | `UNEXPECTED_ROOT` | unexpected Chlorine `000057D5`; atmospheric/Common collision |
| Bara VII-d | `0005E39F` | `UNEXPECTED_ROOT` | unexpected Nickel `000057CB`; likely sixth distinct Common family / unresolved five-family guard |

The Chlorine and Bara interpretations retain their existing evidence boundaries;
this correction adds no collision or family-count heuristic.
