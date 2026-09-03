# Brief 10E — Baseline command-line interface and runtime path controls

## Status

Implementation brief for `gooberpede/starfield-resource-reproducer`.

This brief follows the completed 10D default product exporter. The reproducer now has a reliable canonical production pipeline and a clean default product:

```text
biome-inorganic-resources.csv
```

10E turns the current minimal/internal CLI into the first stable end-user command-line interface.

This brief is deliberately limited to the **baseline production CLI**.

Do **not** implement diagnostic modes yet.
Do **not** reintroduce oracle-based validation.
Do **not** modify xEdit scripts.
Do **not** modify `starfield-outpost-network`.
Do **not** commit or push unless explicitly asked.

## 1. Current CLI state

Inspect `src/starfield_resource_reproducer/cli.py`.

The current CLI still reflects earlier research/validation phases, including options such as:

```text
--validate-all
--all
--export-biome-resources
--data-dir
--atmosphere-data
```

and currently prints help when invoked with no arguments.

10E should replace that research-oriented command surface with the agreed production CLI.

Historical/internal validation functions may remain in code/tests where still useful, but they should not define the new default user experience.

## 2. Core default behavior

A bare invocation:

```text
starfield-resource-reproducer
```

must run the normal production pipeline:

```text
resolve canonical inputs
→ load inputs
→ validate input schemas/coherence
→ generate terrestrial results
→ build enriched accepted occurrences
→ build/validate clean product
→ write biome-inorganic-resources.csv
```

Validation is always part of production.

Do not require a separate `--export-*` switch for ordinary use.
Do not print help merely because no arguments were supplied.

## 3. Baseline public options

Implement:

```text
--help
--version

--quiet
--verbose

--no-overwrite

--resource-generation-file PATH
--resource-tree-file PATH
--atmospheric-resources-file PATH
--planet-directory-file PATH

--output PATH
--manifest

--validate-only
```

Do not implement a public `--diagnostic-mode` yet.
Do not implement oracle-validation options.

## 4. `--help`

Use normal `argparse` help behavior.

Help text should concisely explain:

- what the program produces;
- default input behavior;
- default output behavior;
- input override options;
- output path semantics;
- `--manifest`;
- `--no-overwrite`;
- `--validate-only`;
- `--quiet` / `--verbose`.

Do not expose unnecessary reverse-engineering detail in ordinary help.

## 5. `--version`

Emit:

```text
starfield-resource-reproducer 1.0.0
```

using the actual package version rather than a hard-coded literal.

Exit `0` without loading data or generating output.

## 6. Exit-code contract

Use:

```text
0 = success
1 = runtime/data/validation/output failure
2 = command-line usage error
```

Examples of exit `1`:

```text
missing/unreadable input file
invalid canonical CSV
cross-input coherence failure
generation/product invariant failure
unwritable output path
--no-overwrite collision
filesystem creation/write failure
```

Examples of exit `2`:

```text
unknown option
missing option value
mutually incompatible options
invalid --output command-line form
--quiet + --verbose
```

Allow `argparse` to retain conventional exit-2 usage-error behavior where practical.

Do not invent a large custom exit-code taxonomy.

## 7. Runtime error presentation

For ordinary runtime/data failures:

- print a concise human-readable error to stderr;
- identify the relevant file/path/condition where possible;
- return exit `1`;
- do not dump an uncaught traceback during normal CLI use.

`--verbose` is not a traceback/debug mode.

Never prompt interactively for overwrite confirmation.

## 8. Canonical input defaults

Default production inputs remain:

```text
planet-resource-generation.csv
ires-hierarchy.csv
planet-atmospheric-resources.csv
planet-directory.csv
```

from the reproducer's canonical bundled/project `data/` location.

Default input resolution must **not** depend on the current working directory containing a `data/` folder.

The validation oracle `planet-all-resources.csv` is not a production dependency and must not be loaded by the baseline CLI.

## 9. Input override options

Implement:

```text
--resource-generation-file PATH
--resource-tree-file PATH
--atmospheric-resources-file PATH
--planet-directory-file PATH
```

Each overrides only its corresponding default input.

Absolute paths are accepted.
Relative paths resolve from the user's current working directory.

A missing/unreadable explicit input path is runtime failure `1`, not usage error `2`.

Do not silently fall back to the default file when an explicit override fails.

## 10. Remove or internalize old aggregate input controls

The public baseline should not require `--data-dir`.

If an internal/base-data-directory parameter remains useful for tests/package structure, keep it internal or hidden only if necessary.

Replace legacy public `--atmosphere-data` with `--atmospheric-resources-file`.

Avoid ambiguity between an aggregate data directory and individual file overrides.

## 11. `--output` accepted forms

`--output PATH` may specify:

```text
a directory
a CSV filename
a directory + CSV filename
```

Examples:

```text
--output .
--output output
--output output\
--output C:\Exports
--output C:\Exports\
--output my-resources.csv
--output C:\Exports\my-resources.csv
```

Apply these resolution rules in order.

### Existing directory

If `PATH` exists and is a directory:

```text
PATH/biome-inorganic-resources.csv
```

### Explicit/trailing directory syntax

If `PATH` ends with a platform-appropriate path separator:

- treat it as a directory;
- create it if needed;
- write `biome-inorganic-resources.csv` inside it.

### Non-existent path with `.csv`

If `PATH` does not exist and ends in `.csv` case-insensitively, treat it as the explicit output file path.

### Non-existent path without `.csv`

Treat it as a directory path:

- create it if needed;
- write `biome-inorganic-resources.csv` inside it.

### Existing file

If `PATH` exists and is a file:

- it must have a `.csv` suffix;
- treat it as the explicit output CSV target.

An explicit output filename using another extension is usage error `2`.

Do not silently append `.csv` to a filename-like value with another extension.

## 12. Explicit output path failure behavior

When `--output` is explicitly supplied:

- use the resolved destination requested by the user;
- create missing parent directories where appropriate;
- if it cannot be created/written, fail with exit `1`;
- **do not fall back** elsewhere.

Explicit intent must not be silently redirected.

## 13. Default output resolution

When `--output` is not supplied:

Preferred destination:

```text
./output/biome-inorganic-resources.csv
```

where `.` is the caller's current working directory.

Rules:

```text
1. If ./output exists and is usable:
       use it.

2. If ./output does not exist:
       attempt to create it and use it.

3. If ./output cannot be created or used:
       fall back to:
       ./biome-inorganic-resources.csv

4. If fallback is also unwritable:
       fail with exit 1.
```

When fallback occurs, print an informational message in normal/verbose mode.
`--quiet` suppresses that informational message.

Do not use the package installation directory as the default output location.

## 14. Overwrite policy

Overwrite is the default.

If the target CSV exists and `--no-overwrite` is absent:

```text
replace it after successful production
```

Do not ask for confirmation.
Do not invent a new filename.
Do not add timestamps/counters.

## 15. `--no-overwrite`

`--no-overwrite` means:

> Do not replace an existing requested output artifact.

It does **not** require `--output`.

This is valid:

```text
starfield-resource-reproducer --no-overwrite
```

Never prompt `[y/N]`.
Never auto-select a new filename.

On collision, print a clear error and exit `1`.

## 16. Manifest default behavior

Manifest is **off by default**.

Ordinary run normally writes only:

```text
biome-inorganic-resources.csv
```

Do not generate a new manifest unless:

1. `--manifest` was requested; or
2. a sibling manifest already exists and must therefore be refreshed to avoid becoming stale.

## 17. `--manifest`

When `--manifest` is supplied, generate the CSV and manifest from the **same in-memory production run metadata**.

Do not generate the manifest later by re-reading the CSV and inspecting whatever inputs happen to exist at that later moment.

The manifest must use the same:

```text
ExportTimestamp
ReproducerVersion
input hashes/metadata
row count
```

associated with the produced CSV run.

## 18. Manifest name and location

The manifest always accompanies the resolved CSV and derives mechanically from its filename.

Examples:

```text
C:\Exports\myResourceFile.csv
C:\Exports\myResourceFile.manifest.json
```

and:

```text
./output/biome-inorganic-resources.csv
./output/biome-inorganic-resources.manifest.json
```

Do not add a separate manifest-path option.

## 19. Existing-manifest collision rule without `--manifest`

If the user runs without `--manifest`, but the resolved sibling manifest already exists, a successful overwrite run must **refresh that manifest** from the same run metadata rather than deleting it, leaving it stale, or aborting solely because it exists.

Required behavior:

```text
CSV exists, no manifest, no --manifest:
    replace CSV only

CSV exists, manifest exists, no --manifest:
    replace CSV
    regenerate manifest

CSV exists, no manifest, --manifest:
    replace CSV
    create manifest

CSV exists, manifest exists, --manifest:
    replace both
```

Invariant:

> If a sibling manifest exists after a successful production run, it describes the CSV produced by that run.

## 20. `--no-overwrite` + manifest semantics

Without `--manifest`:

```text
if CSV exists:
    abort with exit 1
```

The sibling manifest is not an independent collision condition.

If CSV does not exist but a sibling manifest exists:

- production may proceed;
- write the new CSV;
- refresh the pre-existing manifest from the same run metadata.

With `--manifest`:

```text
if CSV exists OR manifest exists:
    abort with exit 1
```

Do not write either artifact.

## 21. Atomic output behavior

Preserve/extend 10D atomic-writing behavior.

Production must not leave partial CSV or manifest files after failure.

When a manifest will be written/refreshed, prepare both output contents from the same successful in-memory production result before replacing final destinations.

Pair-level filesystem transactions are not required.

## 22. `--quiet`

`--quiet` suppresses normal informational/progress output.

It must **not** suppress warnings or errors.

Examples suppressed:

```text
resolved output destination
normal row-count summary
manifest-written notification
normal validation-success summary
```

## 23. `--verbose`

`--verbose` adds operational detail without becoming a reverse-engineering diagnostic mode.

Useful detail includes:

```text
resolved canonical input paths
resolved output CSV path
resolved manifest path/action
input row/body counts
major validation/generation stages
generated BIOME/ATMOSPHERE row counts
elapsed time if straightforward
fallback output-location notice
```

Do not print per-planet generation diagnostics, RNG traces, family-cache details, or occurrence dumps.

## 24. `--quiet` and `--verbose`

They are mutually exclusive.

Supplying both is usage error `2`.

Use an argparse mutually exclusive group where practical.

## 25. Validation is always performed

Normal production always performs:

```text
load
→ validate source schemas/coherence
→ generate
→ validate generation/product invariants
→ write
```

There is no less-safe normal mode.

Do not add `--no-validate`.

## 26. `--validate-only`

`--validate-only` runs the same production/validation pipeline but writes no artifacts:

```text
load inputs
→ validate inputs/coherence
→ generate
→ build product
→ validate product invariants
→ write nothing
```

It does **not** mean "perform extra validation."

Success: exit `0`.
Runtime/validation failure: exit `1`.

## 27. `--validate-only` incompatible options

Reject these with usage error `2`:

```text
--validate-only + --output
--validate-only + --manifest
--validate-only + --no-overwrite
```

Input overrides remain valid.
`--quiet` and `--verbose` remain valid.

## 28. No oracle validation

Do not load or compare against `planet-all-resources.csv` as part of the baseline CLI.

The user cannot be assumed to possess it and it may be stale for future game/plugin versions.

Existing developer/research regression tests may still use it internally.

## 29. Diagnostic mode deliberately deferred

Do not implement:

```text
--diagnostic-mode
--add-generation-data
```

in 10E.

Future diagnostic design may support multiple modes. Do not prematurely freeze mode names or output contracts here.

## 30. CLI architecture

Keep CLI concerns separate from domain/generation/product logic.

Prefer:

```text
parse CLI
→ resolve paths/options
→ invoke production service
→ render concise status/errors
→ return exit code
```

If useful, add small typed/configuration values for resolved runtime options rather than passing a large argparse namespace through the model.

## 31. Production API refactor

The current 10D production/export function may assume repository-root paths and fixed output locations.

Refactor as needed so the CLI can provide:

```text
four resolved canonical input paths
resolved output CSV path
whether a manifest is required/refreshed
production timestamp
```

without duplicating product construction.

Keep one production path.

Tests should invoke the same core functions with temporary paths.

## 32. Default input versus output path semantics

Document the intentional distinction:

```text
default inputs:
    package/project canonical data location

default outputs:
    caller's current working directory
```

This prevents installed software from attempting to write into package/program files.

## 33. Help examples

Include a few useful examples in README/help documentation:

```text
starfield-resource-reproducer
starfield-resource-reproducer --manifest
starfield-resource-reproducer --output C:\Exports
starfield-resource-reproducer --output C:\Exports\my-resources.csv --manifest
starfield-resource-reproducer --no-overwrite
starfield-resource-reproducer --validate-only
```

Also show a four-input override example.

## 34. Tests — parser and usage behavior

Add focused CLI tests for at least:

```text
--help exits 0
--version exits 0 and prints expected version
unknown option exits 2
missing option argument exits 2
--quiet + --verbose exits 2

--validate-only + --output exits 2
--validate-only + --manifest exits 2
--validate-only + --no-overwrite exits 2
```

Use temporary directories.

## 35. Tests — output path resolution

Test:

```text
no --output:
    creates/uses ./output/

default ./output unusable:
    falls back to CWD file

existing directory --output:
    uses default CSV name inside directory

nonexistent no-extension --output:
    creates directory and uses default CSV name

nonexistent .csv --output:
    treats as explicit filename

directory + explicit filename:
    writes exact target

explicit non-.csv filename:
    usage error

explicit unwritable path:
    runtime failure with no fallback
```

Where permissions are platform-dependent, mock/inject the filesystem decision rather than relying on brittle OS behavior.

## 36. Tests — overwrite semantics

Test:

```text
default overwrite replaces existing CSV

--no-overwrite + existing CSV:
    exit 1
    existing file unchanged

--no-overwrite with no collision:
    succeeds

no interactive prompt occurs
```

## 37. Tests — manifest semantics

Test:

```text
no --manifest, no sibling manifest:
    CSV only

--manifest:
    CSV + sibling manifest

custom CSV filename + --manifest:
    <custom-stem>.manifest.json beside CSV

no --manifest + existing sibling manifest:
    CSV replaced
    manifest refreshed

--manifest + --no-overwrite + CSV exists:
    abort, neither replaced

--manifest + --no-overwrite + manifest exists:
    abort, neither replaced

no --manifest + --no-overwrite + CSV absent + sibling manifest exists:
    CSV written
    existing manifest refreshed
```

Assert refreshed manifests use the same production metadata/timestamp as the produced CSV.

## 38. Tests — input overrides

For each of the four input options:

- verify explicit path is used;
- verify relative path resolves from CWD;
- verify missing explicit path exits `1`;
- verify no fallback occurs after explicit-path failure.

Also verify a bare run from a CWD with no `data/` directory still finds default canonical inputs.

## 39. Tests — quiet/verbose

Verify:

```text
--quiet:
    suppresses normal informational output
    retains error output

--verbose:
    includes resolved paths/stage details
    does not emit generation diagnostics
```

Avoid excessively brittle wording assertions.

## 40. Tests — validate-only

Verify:

```text
--validate-only:
    executes the same product-building validation path
    writes no CSV
    writes no manifest
    returns 0 on valid canonical inputs
```

Use a deliberately invalid input/coherence fixture to verify exit `1` with no artifacts.

## 41. Full regression

Run the full suite.

Current baseline before 10E:

```text
156 passed
```

Run canonical generation validation:

```text
1,444 / 1,444 exact
0 mismatches
0 errors
```

Regenerate the default product through the new bare CLI and confirm:

```text
7,780 total rows
7,445 BIOME rows
335 ATMOSPHERE rows
```

unless the canonical inputs have deliberately changed.

Also verify Volii Alpha:

```text
0 BIOME
2 ATMOSPHERE
```

Run:

```text
python scripts/check_mojibake.py
git diff --check
```

and all UTF-8 safeguards.

## 42. Documentation

Update current-state documentation, at minimum:

```text
README.md
AGENTS.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/BIOME-INORGANIC-RESOURCES.md
```

Document the stable baseline CLI contract.

Make clear that:

- validation is always part of normal production;
- `--validate-only` suppresses writing only;
- oracle validation is not an end-user runtime dependency;
- diagnostic modes are deferred.

Do not rewrite historical implementation briefs/experiments.

## 43. Out of scope

Do **not** implement:

```text
diagnostic modes
multiple diagnostic products
RNG trace output
family-cache reports
per-planet selection
interactive prompts
configuration files
environment-variable configuration
alternate output formats
oracle-validation CLI
GUI
packaging/installer changes
shell completion
logging framework overhaul
```

These may be considered later.

## Acceptance criteria

10E is complete when:

1. bare invocation produces the normal validated CSV product;
2. `--help` and `--version` behave conventionally;
3. all four canonical inputs can be overridden individually;
4. default inputs are independent of CWD;
5. default output prefers `./output/` and falls back to CWD only when necessary;
6. explicit `--output` supports directory, filename, or both under the agreed rules;
7. overwrite is default and `--no-overwrite` aborts without prompting;
8. manifest is off by default;
9. `--manifest` creates the sibling manifest;
10. an existing sibling manifest is automatically refreshed on later CSV overwrite even without `--manifest`;
11. CSV and manifest share the same in-memory run metadata;
12. `--validate-only` performs the normal validated run but writes nothing;
13. `--quiet`/`--verbose` are mutually exclusive and behave as agreed;
14. exit codes follow `0 / 1 / 2`;
15. runtime CLI does not depend on the validation oracle;
16. diagnostic modes remain unimplemented;
17. existing 10D product and protected generation behavior remain unchanged.

## Deliverable report

Report:

1. files changed;
2. public CLI option list;
3. removed/replaced legacy CLI options;
4. default input-resolution behavior;
5. explicit input override behavior;
6. default output-resolution behavior;
7. `--output` resolution rules implemented;
8. overwrite/no-overwrite behavior;
9. manifest creation/refresh behavior;
10. validate-only behavior;
11. quiet/verbose behavior;
12. exit-code/error-handling implementation;
13. parser/path/overwrite/manifest/validation tests added;
14. total test result;
15. bare-CLI generated product row counts;
16. canonical 1,444-body generation validation result;
17. mojibake/UTF-8/diff-check results;
18. confirmation no oracle dependency was introduced into runtime CLI;
19. confirmation no diagnostic mode was implemented;
20. confirmation no commit/push was performed.

Suggested commit message after review:

```text
feat: add production command line interface
```
