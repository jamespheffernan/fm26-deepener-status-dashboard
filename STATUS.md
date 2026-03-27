# FM26 Deepener — Project Status

## Goal
Extract rich game data from Football Manager 26 and use LLMs to generate immersive media content (match reports, pundit commentary, press conferences, transfer analysis, newspaper articles, fan forums).

## What We've Done

### HTML Export Parser (Working)
- **Built a standalone parser** for FM's built-in "Print Screen → Web Page" exports
- **No game modding required**: runs entirely on exported `.html` files, so it works on macOS Tahoe right now
- **CLI implemented**: `python3 -m fm_html_extract --input <file-or-dir> --output-dir <dir>`
- **Outputs produced**:
  - `*.clean.csv` — cleaned raw table with stable unique headers
  - `*.records.json` — structured records with typed numeric fields and parsed money ranges
  - `*.summary.json` — row/column counts, numeric stats, top values for key categorical fields
- **FM quirks handled**:
  - Duplicate headers like `Nat` are disambiguated (`nationality`, `natural_fitness`)
  - Attribute/value coercion for ints/floats/heights
  - Wage/transfer/release-clause parsing into min/max numeric helpers
  - Directory input automatically selects the newest HTML export
- **Tested** with FM-style fixtures: 4 passing unit/integration tests via `python3 -m unittest discover -s tests -p 'test_*.py'`

### Snapshot Builder + Prompt Pack (Working)
- **Directory-level snapshot assembly**: parses every `.html` export in a folder and combines them into one save snapshot JSON
- **Export type inference** currently recognizes:
  - `squad`
  - `player_search`
  - `fixtures`
  - `league_table`
- **Prompt pack generation** now creates:
  - `match-report.prompt.md`
  - `press-conference.prompt.md`
  - `transfer-briefing.prompt.md`
  - `snapshot-overview.md`
- **Inferred context**:
  - Detects the primary club name from squad exports
  - Carries optional `save_name`, `club_name`, and `manager_name` into the prompt pack
- **Tested**: parser/snapshot/prompt workflow now has 7 passing tests via `python3 -m unittest discover -s tests -p 'test_*.py'`

### Save File Binary Parser (Major Progress)
- **Save format fully mapped**: `.fm` files = 26-byte SI header + zstd multi-frame payload → 6,887 frames → 587MB decompressed
- **Frame 3 (198MB) deep analysis complete**:
  - Header contains record counts: 131,584 players, 65,800 clubs, 2,028 competitions, 258 nations
  - Game date extracted: **7 Jan 2025** (from your Grenoble v03 save)
- **Core player stats block cracked**:
  - 15 position bytes are stored directly on the 1-20 scale
  - The remaining 54 visible attributes use the classic FMScout/Cheat Engine ordering, but on an internal 0-100 scale (`display ~= round(raw / 5)`)
  - Haaland's real block is confirmed at `0x060DE453` in the original frame and `0x060DE1BB` in the modified frame
  - The modified save flips Haaland's Finishing byte from raw `91` to raw `5`, which decodes to display `18 -> 1`
  - Reputation + CA/PA sit in a fixed preamble 30 bytes before the block
- **Name tables fully cracked and extracted**:
  - **291,128 first names** with IDs (format: `[uint32 id][uint32 len][UTF-8 string]`)
  - **595,757 surnames** with IDs (format: `[uint32 len][UTF-8 string][3-byte id][0x00]`)
  - Names grouped by nationality (~256 names per group, 1,021 groups)
- **24,098 clubs extracted** with full and short names (Arsenal/Arsenal, Grenoble Foot 38/Grenoble, etc.)
- **Date format cracked**: `[uint16 day_of_year][uint16 year]` — confirmed by finding Haaland's DOB (21 Jul 2000) at 12 locations
- **Player record region identified** (0x07000000-0x08000000): contains surname IDs + byte-sized attributes (1-20 scale) + date references
- **Working parser built**: `scripts/fm26_parser.py` extracts names, clubs, and game info from raw saves
- **What remains unknown**: exact player record field layout (which byte offset = which attribute). Would need Cheat Engine tables or il2cpp metadata to fully map.
- **Full research doc**: `research/binary-format-findings.md`

### BepInEx Plugin Approach (Blocked)
We attempted to build a BepInEx plugin for FM26 (the approach used by the FM26 Camera Mod and Player Export mods). This would have given direct access to the game's data model at runtime.

**What we built:**
- `.csproj` project targeting BepInEx 6 IL2CPP (net6.0)
- `Plugin.cs` — BepInEx entry point
- `TypeDiscovery.cs` — F10 key dumps all game classes to a text file
- `DataExporter.cs` — F11 key exports game data to JSON (stub, pending type discovery)
- `deploy.sh` — builds and copies DLL to BepInEx/plugins/
- `doorstop_shim/` — custom arm64e injection shim for macOS Tahoe

**Why it's blocked — macOS 26 (Tahoe) arm64e enforcement:**

macOS 26 introduced a breaking change: ALL code loaded via `DYLD_INSERT_LIBRARIES` or `dlopen` from injected code must be compiled as `arm64e` (pointer-authenticated ARM64). Standard `arm64` code is rejected.

BepInEx's entire native stack is arm64/x86_64:
- `libdoorstop.dylib` — arm64 + x86_64 (no arm64e)
- `dotnet/libcoreclr.dylib` — x86_64 only (BepInEx ships x86_64 CoreCLR for macOS)
- All other `dotnet/*.dylib` runtime libraries — x86_64

We tried:
1. ✅ Built arm64e shim that successfully injects into FM26
2. ❌ Shim can't dlopen the arm64 doorstop (arm64e process rejects arm64 dlopen)
3. ❌ Swapped BepInEx x86_64 CoreCLR with system arm64 CoreCLR — still rejected by arm64e
4. ❌ Header-patching arm64→arm64e — internal bind opcodes differ, crashes with "bad bind opcode"
5. ❌ Rosetta (x86_64 mode) — macOS 26 still enforces arm64e even under Rosetta

**Bottom line**: BepInEx cannot work on macOS 26 Tahoe until the BepInEx team ships arm64e-compiled native libraries. This is a known gap — no FM26 mods work on macOS Tahoe currently.

### Game Installation Analysis (Complete)
- **FM26 location**: `~/Library/Application Support/Steam/steamapps/common/Football Manager 26/`
- **Save location**: `~/Library/Application Support/Sports Interactive/Football Manager 26/games/`
- **Match replays**: `.rec` and `.pkm` files in `matches/automatic/{competition}/`
- **Caches**: `.skc` files for narratives, press conferences, media, backroom advice
- **Unity + il2cpp**: GameAssembly.dylib (183MB universal binary), no Managed/ DLLs

## Viable Next Steps (Ranked)

### 1. Expand the FM Built-In HTML Export Pipeline (Best Current Path)
- Create custom views in FM26 showing player attributes, league tables, fixtures, schedules, inbox/news, and competition tables
- Export via Ctrl+A → Ctrl+P → Web Page
- Build a combined snapshot with `python3 -m fm_html_extract --input <export-dir> --output-dir <artifact-dir> --snapshot --generate-prompts`
- Feed the generated snapshot JSON and prompt markdown directly to LLMs for media generation
- **Pros**: Works on any OS, no modding needed, well-established (pyscoutfm, FMDataLab use this)
- **Cons**: Manual export step, limited to data you can display in FM views
- **Immediate next build-out**:
  - Add more export types (news/inbox, transfers, staff, schedule, competition stats)
  - Improve cross-export joins so a player can be traced across squad/search/news exports
  - Add prompt packs for fan forums, newspaper back pages, pre-match previews, and transfer rumours

### 2. Direct Save File Parser (Partially Working)
- Names and clubs already extractable via `scripts/fm26_parser.py`
- Player records located but field layout not yet mapped
- Next steps: use Cheat Engine tables (FearLess Revolution FM26 tables) to map attribute offsets
- Could also use il2cpp metadata from GameAssembly.dylib to get class field definitions
- **Pros**: No game running needed, full access to all data, automated
- **Cons**: Field layout changes with each FM update, attribute mapping still incomplete

### 3. Wait for BepInEx arm64e Support
- Monitor BepInEx GitHub for macOS Tahoe fixes
- The arm64e issue affects all BepInEx IL2CPP mods on macOS 26
- Could contribute a PR to the BepInEx/UnityDoorstop repos
- **Pros**: Gives full runtime access to game objects
- **Cons**: Unknown timeline, depends on upstream

### 4. Use a Windows VM / Boot Camp
- Run FM26 + BepInEx on Windows where there are no arm64e issues
- Our plugin code (`Plugin.cs`, `TypeDiscovery.cs`, `DataExporter.cs`) is ready to deploy
- **Pros**: Everything works, existing mod ecosystem
- **Cons**: Requires Windows license, running a VM

## Files Created

```
FM26 Deepener/
├── fm_html_extract/
│   ├── __init__.py                       # Python package for FM HTML export parsing
│   ├── __main__.py                       # CLI entrypoint: python3 -m fm_html_extract
│   ├── parser.py                         # HTML table parsing, normalization, JSON/CSV output
│   ├── snapshot.py                       # Multi-export snapshot assembly + export type inference
│   └── prompts.py                        # LLM-ready prompt pack generation from snapshots
├── scripts/
│   ├── fm26_parser.py                    # Main parser: extracts names, clubs, game info from .fm saves
│   ├── decompress_save.py               # Decompress .fm save into individual zstd frames
│   ├── analyze_frame3.py                # String extraction, type tags, stride analysis
│   ├── crack_name_tables.py             # Full name table extraction (291K first + 596K surnames)
│   ├── find_player_records.py           # DOB and surname ID location search
│   ├── compare_player_records.py        # Multi-player record alignment comparison
│   └── (+ 5 more analysis scripts)      # deep_dive, map_record, find_record_arrays, etc.
├── output/
│   ├── firstnames.json                  # 291,128 first names with IDs
│   ├── surnames.json                    # 595,757 surnames with IDs
│   ├── clubs.json                       # 24,098 clubs (full + short names)
│   └── game_info.json                   # Game date, version, record counts
├── research/
│   ├── fm-save-file-research.md          # Comprehensive save format research (300+ lines)
│   └── binary-format-findings.md         # Deep binary analysis findings (dates, names, regions)
├── FM26Deepener/
│   ├── FM26Deepener.csproj               # BepInEx plugin project
│   ├── Plugin.cs                          # BepInEx entry point
│   ├── TypeDiscovery.cs                   # F10 → dump all game classes
│   ├── DataExporter.cs                    # F11 → export game data (stub)
│   └── deploy.sh                          # Build + deploy script
├── doorstop_shim/
│   ├── doorstop_arm64e.c                  # arm64e DYLD injection shim
│   └── libdoorstop_shim.dylib            # Compiled shim (works, but can't load arm64 code)
├── tests/
│   ├── fixtures/
│   │   ├── player_search_export.html     # FM-style HTML export fixture
│   │   ├── fixtures_export.html          # FM-style fixtures export fixture
│   │   ├── league_table_export.html      # FM-style league table export fixture
│   │   └── squad_export.html             # FM-style HTML export fixture
│   └── test_fm_html_extract.py           # Parser + CLI tests
└── STATUS.md                              # This file
```

### Your Save Files
| Save | Size |
|------|------|
| Cesar Jules - Grenoble (v03) | 165 MB |
| Cesar Jules - Grenoble (v02) | 162 MB |
| James Heffernan - Cambridge - declining Tot | 183 MB |
| Cesar Jules - Grenoble -- resigning (v02) | 121 MB |
| last save overwrite backup | — |

## Installed on System
- .NET 8 SDK (Homebrew, arm64)
- Python 3.14.3 with venv at `.venv/` (zstandard 0.25.0 installed)
- BepInEx 6 build 755 extracted to FM26 game root (non-functional on Tahoe)
- arm64 CoreCLR swapped in (non-functional due to arm64e requirement)

## Current Recommendation
Use the HTML export pipeline now, not the BepInEx path.

Example:

```bash
python3 -m fm_html_extract \
  --input "~/fm-exports" \
  --output-dir "./artifacts/html_exports" \
  --snapshot \
  --generate-prompts \
  --print-summary
```

If `--input` is a directory and `--snapshot` is omitted, the parser automatically picks the newest `.html` export in that folder.
