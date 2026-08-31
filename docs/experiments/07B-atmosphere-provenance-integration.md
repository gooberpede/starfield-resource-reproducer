# Brief 07B Post-Integration Validation

## Scope

This run integrates the atmospheric TSV, provenance-aware occurrences, the
shared eight-unique-FormID state, pre-main Everywhere traversal, and the recovered
category-generic Special/Common selector. It applies no residual-mismatch heuristic.

The comparison channel remains the RSGD/CK-visible prediction because
`planet-all-resources.csv` is proven to omit at least some ATMO-only resources.
Atmospheric inputs and the final player-facing union remain separate result channels.

## Headline comparison

```text
                         Pre-07B   Post-07B
population                  1,444      1,444
exact                       1,281      1,426
mismatches                    163         18
exact rate                 88.71%      98.75%
generation errors               0          0
coverage-only bodies            0          0
```

Post-07B mismatch directions:

```text
prediction-only              3
oracle-only                 15
both-sides                   0
missing occurrences         15
unexpected occurrences       3
```

## Residual stratification

```text
predicted unique count
  1: 2
  2: 2
  3: 2
  4: 1
  5: 3
  6: 3
  7: 2
  8: 3

atmospheric present         14
atmospheric absent           4
Everywhere present           3
Everywhere absent           15
Special present              0
Special absent              18
single-biome                 0
multi-biome                 18
capacity reached             6
capacity not reached        12
```

Full-corpus provenance mismatch count is not currently measurable because there
is no independent expected-provenance oracle for the complete generation chain.
Final-set equality must not be interpreted as provenance equality. The atmospheric
channel reproduces its loader input by construction and integrity checks; this is
not an independent atmospheric oracle.

The fresh machine-readable residual report is
`validation/full-canonical-mismatches.csv`.

## Interpretation boundary

The 18 residual mismatches are input to later research. Brief 07B stops here and
does not infer the SurveyAggregator contract, add vapor exceptions, or introduce
planet-specific repairs.
