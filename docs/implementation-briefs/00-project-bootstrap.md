# Implementation Brief 00 — Project Bootstrap

## Context

Repository:

```text
gooberpede/starfield-resource-reproducer
```

The repository is already initialized and committed. It contains the project documentation, directory scaffold, `.gitignore`, and the three canonical CSV inputs under `data/`.

Authoritative documentation already present:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md
```

Canonical data already present:

```text
data/PlanetResourceGeneration_v5.csv
data/Starfield_IRES_Hierarchy.csv
data/planet-all-resources.csv
```

The deprecated dataset:

```text
Starfield_InorganicResources_Canonical.csv
```

must not be introduced or used.

At the start of this brief there is intentionally no Python implementation scaffold:

- no `pyproject.toml`;
- no `reproduce.py`;
- no Python package under `src/`;
- no implemented resource-generation logic.

This brief is **bootstrap only**. Establish a clean, reproducible Python development environment and the smallest executable/testable application skeleton needed for later briefs.

## Goal

Create a conventional, minimal Python project scaffold that:

1. can be installed in editable mode;
2. has a package under `src/`;
3. has a thin root-level `reproduce.py` launcher;
4. has a minimal CLI that can display help/version information;
5. has a working pytest setup;
6. leaves all Starfield generation/data-loading logic for later briefs.

## Required Pre-Implementation Reading

Before editing, read:

```text
AGENTS.md
README.md
docs/ARCHITECTURE.md
docs/BACKLOG.md
docs/DOMAIN-RULES.md
docs/IMPLEMENTATION-WORKFLOW.md
```

Then inspect the current repository tree and existing `.gitignore`.

Treat those files as authoritative. If the repository differs materially from this brief, preserve existing intentional work and report the difference rather than overwriting it blindly.

## Required Changes

### 1. Create `pyproject.toml`

Create a small standards-based Python project definition.

Use:

```text
project name: starfield-resource-reproducer
initial version: 0.1.0
minimum Python: 3.12
```

The import/package name should be:

```text
starfield_resource_reproducer
```

Use a conventional `src/` layout.

A simple setuptools build backend is appropriate. Do not introduce Poetry, Hatch, PDM, uv-specific project metadata, or another project-management framework in this brief.

There should be **no required runtime third-party dependencies yet**.

Add pytest as a development/test dependency, preferably:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
]
```

Configure pytest in `pyproject.toml` so `tests/` is the test root.

Do not add pandas, numpy, click, typer, rich, pydantic, or other libraries at this stage.

### 2. Create the package skeleton

Create:

```text
src/
└── starfield_resource_reproducer/
    ├── __init__.py
    └── cli.py
```

#### `__init__.py`

Expose the package version simply:

```python
__version__ = "0.1.0"
```

Avoid elaborate version-management machinery.

#### `cli.py`

Implement a minimal standard-library `argparse` CLI supporting:

```text
--help
--version
```

With no substantive command yet, it may print help and exit successfully.

Do **not** implement future options yet:

```text
--planet
--all
--diagnostic
--mismatches
```

The CLI must not read CSV files in this brief.

### 3. Create the root launcher

Create:

```text
reproduce.py
```

It must be intentionally thin, conceptually:

```python
from starfield_resource_reproducer.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

Do not place application/domain logic in `reproduce.py`.

### 4. Create a minimal test suite

Create:

```text
tests/
├── test_package.py
└── test_cli.py
```

Tests should verify bootstrap behavior only.

At minimum:

- package imports successfully;
- package exposes version `0.1.0`;
- `--help` exits successfully and returns recognizable help text;
- `--version` exits successfully and reports `0.1.0`.

Prefer testing `main()` directly where practical rather than spawning unnecessary subprocesses.

No tests should depend on canonical CSV contents yet.

### 5. Update `.gitignore` conservatively

Preserve all existing entries.

Add standard Python artifacts if not already covered:

```text
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
*.egg-info/
build/
dist/
```

Do not remove existing research/scratch/export exclusions.

Do not ignore `data/` or its canonical CSV files.

### 6. Implementation-brief directory

The documented workflow proposes:

```text
docs/implementation-briefs/
```

If absent, create it only if useful for the repository workflow. Use a `.gitkeep` or small README if Git needs a tracked file.

Do not automatically copy this brief into the repository unless the user explicitly asks Codex to do so.

## Explicit Non-Goals

Do not implement any Starfield algorithm behavior in Brief 00.

Specifically, do not implement:

- CSV parsing;
- FormID normalization;
- PNDT/BIOM/RSGD domain objects;
- IRES graph construction;
- MT19937;
- biome shuffling;
- Special/Common/Everywhere selection;
- descendant generation;
- family caching;
- canonical validation;
- mismatch reports;
- worked-case fixtures;
- `--planet`;
- `--all`;
- planner integration;
- GUI/web/database functionality.

Do not create empty placeholder modules for every file named in `docs/ARCHITECTURE.md` merely to make the tree look complete. Create modules when a brief gives them a real responsibility.

## Environment Setup

The repository should work with a normal Windows virtual environment.

A clean setup should be possible using commands equivalent to:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

If the local Python launcher differs, use the available Python 3.12+ executable rather than changing project requirements solely to fit the machine.

Do not commit `.venv`.

## Required Validation

Run the equivalent of:

```powershell
.\.venv\Scripts\python -m pytest
```

```powershell
.\.venv\Scripts\python reproduce.py --help
```

```powershell
.\.venv\Scripts\python reproduce.py --version
```

and:

```powershell
.\.venv\Scripts\python -c "import starfield_resource_reproducer; print(starfield_resource_reproducer.__version__)"
```

Expected version:

```text
0.1.0
```

## Acceptance Criteria

Brief 00 is complete when:

- [ ] `pyproject.toml` exists and defines a Python 3.12+ project named `starfield-resource-reproducer`.
- [ ] The package lives under `src/starfield_resource_reproducer/`.
- [ ] Editable install succeeds with the development dependency group.
- [ ] There are no required runtime third-party dependencies.
- [ ] `reproduce.py` is a thin launcher only.
- [ ] `python reproduce.py --help` succeeds.
- [ ] `python reproduce.py --version` reports `0.1.0`.
- [ ] `pytest` succeeds.
- [ ] `.gitignore` excludes standard Python/venv/test/build artifacts while preserving existing project exclusions.
- [ ] The three files in `data/` remain unchanged.
- [ ] No deprecated canonical CSV is introduced.
- [ ] No resource-generation or data-loading logic has been implemented.
- [ ] Existing architecture/domain documentation is not rewritten merely to match the scaffold.

## Expected Repository Shape After Brief 00

```text
.
├── .gitignore
├── AGENTS.md
├── README.md
├── pyproject.toml
├── reproduce.py
├── data/
│   ├── PlanetResourceGeneration_v5.csv
│   ├── Starfield_IRES_Hierarchy.csv
│   └── planet-all-resources.csv
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BACKLOG.md
│   ├── DOMAIN-RULES.md
│   └── IMPLEMENTATION-WORKFLOW.md
├── src/
│   └── starfield_resource_reproducer/
│       ├── __init__.py
│       └── cli.py
└── tests/
    ├── test_cli.py
    └── test_package.py
```

Preserve any additional intentional existing files/directories.

## Documentation Updates

This brief should require little or no documentation editing because the existing docs already describe the intended bootstrap.

Update documentation only if implementation exposes a concrete discrepancy.

It is reasonable to mark only the corresponding **Phase 0 — Repository Bootstrap** items complete in `docs/BACKLOG.md` once genuinely satisfied.

Do not mark later backlog phases complete.

For:

```text
Add canonical data files under an agreed local/data path
```

the files were already present before Codex began; Codex may verify and mark that item complete, but should not claim to have created them.

## Commit Guidance

Prefer one small bootstrap commit:

```text
chore: bootstrap Python project
```

If documentation/backlog bookkeeping is separated, an optional second commit may be:

```text
docs: record bootstrap completion
```

Do not mix future algorithm implementation into the bootstrap commit.

## Codex Completion Report

When finished, report:

1. files created;
2. files modified;
3. Python version used for validation;
4. environment/install commands run;
5. pytest result;
6. CLI validation results;
7. any deviations from this brief;
8. any questions or blockers discovered for Brief 01.

Do not begin Brief 01 automatically.
