# FM26 Deepener — Project Status

## Goal
Extract rich game data from Football Manager 26 and use LLMs to generate immersive media content such as match reports, press conferences, transfer briefings, newspaper back pages, and fan-forum style writing.

## Current Headline
- **Best practical path today**: the HTML export pipeline is the production-ready lane.
- **Binary save work has advanced materially**: `fm_save_extract` now does candidate extraction, person reconciliation, relation tagging/resolution, club-link emission, and targeted contract/staff decoding.
- **Runtime modding is still blocked on macOS Tahoe**: the BepInEx path remains stalled by arm64e requirements.
- **Current verification**: the repo currently has **49 passing tests** via `python3 -m unittest discover -s tests -p 'test_*.py'`
  - 10 test modules total
  - 9 HTML-pipeline tests
  - 40 save-extractor / relation / real-slice tests

## What Works Today

### 1. HTML Export Pipeline (Recommended Now)
- **Standalone parser** for FM's built-in `Print Screen -> Web Page` exports
- **No game modding required**: runs entirely on exported `.html` files, so it works on macOS Tahoe right now
- **CLI implemented**:

```bash
python3 -m fm_html_extract --input <file-or-dir> --output-dir <dir>
```

- **Single-export outputs**:
  - `*.clean.csv` — cleaned raw table with stable unique headers
  - `*.records.json` — structured records with typed numeric fields and parsed money ranges
  - `*.summary.json` — row/column counts, numeric stats, top values for key categorical fields
- **FM quirks handled**:
  - Duplicate headers like `Nat` are disambiguated (`nationality`, `natural_fitness`)
  - Attribute/value coercion for ints/floats/heights
  - Wage/transfer/release-clause parsing into min/max numeric helpers
  - Directory input automatically selects the newest HTML export

### 2. Snapshot Builder + Prompt Pack (Working)
- **Directory-level snapshot assembly**: parses every `.html` export in a folder and combines them into one save snapshot JSON
- **Export type inference currently recognizes 9 export families**:
  - `squad`
  - `player_search`
  - `fixtures`
  - `league_table`
  - `transfers`
  - `staff`
  - `schedule`
  - `competition_stats`
  - `news`
- **Prompt pack generation currently writes 8 files**:
  - `match-report.prompt.md`
  - `press-conference.prompt.md`
  - `transfer-briefing.prompt.md`
  - `fan-forum.prompt.md`
  - `newspaper-back-page.prompt.md`
  - `pre-match-preview.prompt.md`
  - `transfer-rumours.prompt.md`
  - `snapshot-overview.md`
- **Inferred context**:
  - Detects the primary club name from squad exports
  - Carries optional `save_name`, `club_name`, and `manager_name` into snapshot and prompt outputs
- **Current coverage**:
  - HTML pipeline behavior is covered by 9 tests in `tests/test_fm_html_extract.py`

### 3. Save Extraction + Relation Resolution (Active, Useful, Still Incomplete)
- **Save format mapped**: `.fm` files = 26-byte SI header + zstd multi-frame payload
- **Frame 3 analysis is now usable for structured extraction**
  - Header counts: 131,584 players, 65,800 clubs, 2,028 competitions, 258 nations
  - Game date extracted: **7 Jan 2025** from the Grenoble save
- **Known hybrid player block is confirmed**
  - `0x00-0x0E`: 15 position bytes stored directly on the `1-20` scale
  - `0x0F-0x44`: 54 classic FM attributes in FMScout/Cheat Engine order, stored on an internal `0-100` scale
  - Visible display approximation: `display ~= round(raw / 5)` for non-position attributes
  - Haaland remains the strongest verified anchor:
    - Original block: `0x060DE453`
    - Modified block: `0x060DE1BB`
    - Finishing byte: raw `91 -> 5`, display `18 -> 1`
  - Reputation + CA/PA sit in a fixed preamble at `block - 0x1E`
- **Reference data already extracted**
  - `291,128` first names
  - `595,757` surnames
  - `24,098` clubs
  - game info including date/version/header counts

#### Working CLIs

**Reference extractor**

```bash
python3 scripts/fm26_parser.py <save-or-frame>
```

**World extractor**

```bash
python3 -m fm_save_extract \
  --input <save-or-frame> \
  --output-dir <dir> \
  [--raw] \
  [--diff-frame <frame>] \
  [--emit-reference-tables]
```

#### Current `fm_save_extract` outputs
- `game_info.json`
- `clubs.json`
- `people.json`
- `players.json`
- `staff_roles.json`
- `club_links.json`
- `contracts.json`
- `unresolved_candidates.json`
- optional `firstnames.json` / `surnames.json`

#### What the extractor now does
- Enumerates candidate people from hybrid blocks
- Extracts inline full-name / DOB anchors
- Reconciles hybrid-block people with inline-name people into canonical records
- Preserves `alias_person_keys` for canonicalization
- Parses inline relation entries near named-person slices
- Classifies relation tags into:
  - `club_employment`
  - `staff_assignment`
  - `contract_reference`
- Resolves supported club-link patterns into typed `club_links.json` entries
- Attaches `typed_relation_summaries` to people
- Enriches staff roles with typed link refs
- Enriches contracts with best available club-link matches when possible
- Emits unresolved evidence instead of hiding uncertainty

#### What is validated today
- Contract wage / expiry decoding from synthetic diff frames
- Staff-role decoding for `WorkingWithYoungsters` from synthetic diff frames
- Diff-decoder hardening around generic labels / frame order
- Relation-tag classification
- Relation resolution against known control patterns
- Extractor reconciliation of alias keys and inline relation entries
- Real-slice validation via a 6-slice manifest covering:
  - Xabi contract base / raise / expiry
  - Jorge staff family before / after edit
  - Athletic Club control family

#### Current limits
- This is still **not** a complete live-save decoder
- Club and employment resolution is only partially generalized
- Some club-link resolution is still pattern-backed rather than broad-based
- Contract and staff decoding are stronger than before, but still need wider live-save coverage

### 4. BepInEx Plugin Approach (Blocked)
We attempted to build a BepInEx plugin for FM26 to read live game objects at runtime.

**What exists in the repo**
- `.csproj` project targeting BepInEx 6 IL2CPP (`net6.0`)
- `Plugin.cs` — BepInEx entry point
- `TypeDiscovery.cs` — F10 key dumps all game classes
- `DataExporter.cs` — F11 export stub
- `deploy.sh` — build + copy into `BepInEx/plugins/`
- `doorstop_shim/` — custom arm64e injection shim for macOS Tahoe

**Why it's blocked**
- macOS 26 Tahoe requires `arm64e` for code loaded via `DYLD_INSERT_LIBRARIES` / injected `dlopen`
- BepInEx's native macOS stack is still arm64/x86_64, not arm64e
- We proved arm64e injection with the shim, but not a usable runtime bridge into BepInEx/CoreCLR

**Bottom line**
- BepInEx remains blocked on macOS Tahoe until upstream ships arm64e-compatible native libraries

### 5. Status Dashboard (Working)
- A lightweight project tracker dashboard exists under `dashboard/`
- It is generated from live repo state by:

```bash
python3 scripts/build_status_dashboard.py
```

- A publishable bundle is built by:

```bash
python3 scripts/build_status_dashboard_site.py
```

- A GitHub Pages publish helper is available via:

```bash
python3 scripts/publish_status_dashboard_pages.py
```

## Recommended Next Steps

### 1. Use the HTML export pipeline for real content generation now
- Create custom views in FM26 for squad, fixtures, transfers, staff, news, and tables
- Export via Ctrl+A -> Ctrl+P -> Web Page
- Build a combined snapshot with:

```bash
python3 -m fm_html_extract \
  --input "~/fm-exports" \
  --output-dir "./artifacts/html_exports" \
  --snapshot \
  --generate-prompts \
  --print-summary
```

- Feed the generated snapshot JSON and prompt markdown directly to LLMs

### 2. Broaden relation resolution beyond the current control patterns
- Generalize club/person/employment joins across more clubs and staff neighborhoods
- Reduce dependence on fixture-backed or control-slice-specific relation patterns

### 3. Generalize contract and staff decoding across more live families
- Use more supervised edited saves
- Add more real-slice fixtures and manifests
- Promote `club_links.json`, `contracts.json`, and `staff_roles.json` from targeted success cases to broader live-save coverage

### 4. Leave news / inbox / media until joins are trustworthy
- Narrative extraction still depends on stable person/team/competition linkage underneath
- `.skc` cache parsing remains a parallel option once joins are in place

### 5. Keep the BepInEx path deprioritized unless runtime conditions change
- Monitor upstream arm64e support
- Fallback option remains Windows/VM if live runtime access becomes essential

## Key Repo Surface

```text
FM26 Deepener/
├── fm_html_extract/                     # HTML export parser, snapshot builder, prompt pack generation
├── fm_save_extract/                     # World extractor, relation tagging/resolution, reconciliation
├── scripts/                            # Save research scripts + dashboard build/publish helpers
├── tests/                              # 49 tests across 10 modules
├── tests/fixtures/real_slice_manifest.json
│                                        # 6-slice control/edit manifest for real extraction validation
├── output/                             # Extracted firstnames, surnames, clubs, game_info
├── research/                           # Save-format findings and reverse-engineering notes
├── FM26Deepener/                       # BepInEx plugin project (blocked on Tahoe arm64e)
├── doorstop_shim/                      # arm64e shim experiments
├── dashboard/                          # Static status tracker dashboard
├── STATUS.md                           # This file
├── AGENT_HANDOFF.md                    # Binary-decoding handoff brief
└── NEXT_DECODING_BRIEF.md              # Next-stage decoding priorities
```

## Your Save Files
| Save | Size |
|------|------|
| Cesar Jules - Grenoble (v03) | 165 MB |
| Cesar Jules - Grenoble (v02) | 162 MB |
| James Heffernan - Cambridge - declining Tot | 183 MB |
| Cesar Jules - Grenoble -- resigning (v02) | 121 MB |
| last save overwrite backup | — |

## Installed on System
- .NET 8 SDK (Homebrew, arm64)
- Python 3.14.3 with venv at `.venv/` (`zstandard 0.25.0` installed)
- BepInEx 6 build 755 extracted to FM26 game root (non-functional on Tahoe)
- arm64 CoreCLR swapped in previously, still blocked by arm64e requirements

## Current Recommendation
Use the HTML export pipeline now, not the BepInEx path.

Treat `fm_save_extract` as the active automation / reverse-engineering lane: it is no longer just raw research, but it is still not yet a full generalized live-save decoder.
