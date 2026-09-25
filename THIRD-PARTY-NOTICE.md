# Third-party notices and project licence boundary

Copyright (C) 2026 Gooberpede.

Project-authored Python source, xEdit scripts, tests, and documentation for
which the repository owner holds the relevant rights are licensed under the
GNU General Public License, version 3 or (at your option) any later version.
See [LICENSE](LICENSE) for the complete GPLv3 text.

That GPL grant does not relicense third-party material. Starfield, official
names, identifiers, classifications, relationships, and other game-derived
records remain subject to the rights of their respective rightsholders. This
includes the normalized records published in:

- `data/planet-resource-generation.csv`;
- `data/ires-hierarchy.csv`;
- `data/planet-atmospheric-resources.csv`;
- `data/planet-directory.csv`; and
- `data/planet-all-resources.csv`.

The first four files are canonical production inputs. The fifth is a
validation-only oracle and is never loaded by normal production generation.
Their extraction and runtime provenance documents source and transformation;
it does not claim Bethesda/ZeniMax approval or place those records under the
repository's GPL grant. See
[docs/CANONICAL-XEDIT-EXPORTS.md](docs/CANONICAL-XEDIT-EXPORTS.md) for the
maintained extraction contracts.

This repository distributes normalized technical, modding, and reference data.
It does not distribute Bethesda game executables, ESM or BA2 archives,
textures, models, audio, complete string tables, or similar raw game assets.

This is an independent, unofficial project. It is not affiliated with or
endorsed by Bethesda Game Studios or Microsoft.
