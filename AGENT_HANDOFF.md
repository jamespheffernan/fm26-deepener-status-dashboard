# FM26 Deepener — Agent Handoff Brief

## Goal
Take the current FM26 world extractor from "good anchored extractions plus targeted relation resolution" to "broader live-save world state with reliable joins across people, clubs, staff roles, and contracts".

## Current Repo State
- **HTML export pipeline is production-ready**
  - `python3 -m fm_html_extract`
  - 9 recognized export types
  - 7 prompt templates plus `snapshot-overview.md`
- **Binary save extraction is now a real extraction surface, not just research**
  - `python3 -m fm_save_extract --input <save-or-frame> --output-dir <dir> [--raw] [--diff-frame <frame>]`
  - Emits:
    - `game_info.json`
    - `clubs.json`
    - `people.json`
    - `players.json`
    - `staff_roles.json`
    - `club_links.json`
    - `contracts.json`
    - `unresolved_candidates.json`
- **Current verification**
  - 49 passing tests total across 10 modules
  - 9 HTML-pipeline tests
  - 40 save-extractor / relation / real-slice tests

## What's Working
- **Save decompression**: `scripts/decompress_save.py` and `fm_save_extract.binary.decompress_main_frame`
- **Reference data extraction**:
  - 291,128 first names
  - 595,757 surnames
  - 24,098 clubs
  - game date / version / header counts
- **Known hybrid player block decode**
  - 15 position bytes on the `1-20` scale
  - 54 classic FM attributes on internal `0-100` values
  - fixed preamble at `block - 0x1E` for reputation + CA/PA
- **Candidate enumeration**
  - `fm_save_extract.player_blocks.enumerate_person_candidates`
  - richer nearby UID / DOB evidence
  - improved dedupe behavior
- **Inline named-person extraction**
  - `fm_save_extract.inline_people.extract_inline_named_people`
  - inline relation windows / relation entries
  - secondary tail parsing (`pat` / `pat2`)
- **Reconciliation**
  - canonical people
  - `alias_person_keys`
  - merged hybrid-block + inline-name identities
- **Relation handling**
  - `fm_save_extract.relation_tags`
  - `fm_save_extract.relation_resolution`
  - typed relation summaries on people
  - typed link refs on staff roles
  - emitted `club_links.json`
- **Supervised diff summaries**
  - `summarize_diff_frames`
  - `summarize_pairwise_diff_frames`
- **Targeted decoders already validated**
  - contract wage / expiry
  - staff `WorkingWithYoungsters`
- **Real-slice validation exists**
  - 6-slice manifest
  - Xabi contract family
  - Jorge staff family
  - Athletic Club control family

## Current Save Files
- **Original (unmodified)**: `frames_claude/frame3.bin` (198.4MB decompressed frame 3)
- **Modified (Finishing 18 -> 1)**: `frames_claude/frame3_modified.bin`
- Source save: `"Cesar Jules - Grenoble (v03) - CLAUDE.fm"` in `~/Library/Application Support/Sports Interactive/Football Manager 26/games/`

## Verified Anchors

### Haaland
```text
Unique ID: 29179241 (0x01BD3D69)
CA: 195, PA: 195
Height: 195cm, Born: 2000-07-21
Home Rep: 8904, Current Rep: 9459, World Rep: 10000
Original block: 0x060DE453
Modified block: 0x060DE1BB
Finishing byte: block + 0x11
Raw change: 91 -> 5
Display change: 18 -> 1
```

### Layout Already Confirmed
- `0x00-0x0E`: 15 position ratings stored directly on the `1-20` scale
- `0x0F-0x44`: 54 classic FM attributes in FMScout/Cheat Engine order, stored on an internal `0-100` scale
- `display ~= round(raw / 5)` for non-position attributes
- Fixed preamble at `block - 0x1E`:
  - `+0x00`: Home Reputation (`uint16`)
  - `+0x02`: Current Reputation (`uint16`)
  - `+0x04`: World Reputation (`uint16`)
  - `+0x06`: CA (`uint16`)
  - `+0x08`: PA (`uint16`)

## What the Extractor Already Emits
- **People**
  - canonical person records
  - merged alias keys
  - typed relation summaries when relation entries exist
- **Players**
  - positions
  - raw attribute values
  - display attribute values
- **Staff roles**
  - decoded `WorkingWithYoungsters`
  - raw + typed link refs
- **Contracts**
  - targeted wage / start / expiry extraction
  - club-key enrichment when matching club links exist
- **Club links**
  - emitted from inline relation entries and staff-role refs
- **Unresolved evidence**
  - metadata clusters
  - low-confidence people
  - inline relation samples
  - diff summaries when comparison frames are supplied

## What Is Still Missing / Unstable
1. **Relation resolution is only partially generalized**
- Some club-link resolution still depends on known control patterns rather than broad decoding.

2. **Staff-side coverage is still targeted**
- Staff-role decoding is stronger, but not yet generalized across many real families.

3. **Contract decoding still needs broader live-save coverage**
- Targeted success exists; broad generalized extraction does not.

4. **News / inbox / media should still wait**
- Those object families depend on reliable joins underneath.

5. **BepInEx remains blocked on Tahoe arm64e**
- Runtime injection experiments are not the shortest path right now.

## Recommended Next Steps

### 1. Broaden relation resolution
- Expand club/person/employment joins beyond the current control-pattern families.

### 2. Generalize staff-side decoding
- Find manager / assistant / coach candidates using DOB, reputation, metadata, and relation patterns.

### 3. Generalize contract decoding with more edited saves
- Best next edits:
  - manager wage change
  - contract expiry change
  - assistant attribute change

### 4. Keep adding real-slice fixtures
- Lock in new control/edit families with manifest-backed tests before broadening heuristics.

### 5. Leave news/media until joins are trustworthy
- Narrative objects are downstream of club/person/competition linkage.

## Key Files
- `fm_save_extract/__main__.py` — world extractor CLI
- `fm_save_extract/extractor.py` — world-state assembly + reconciliation
- `fm_save_extract/inline_people.py` — inline-name / relation-entry parsing
- `fm_save_extract/player_blocks.py` — hybrid block decode + candidate enumeration
- `fm_save_extract/relation_tags.py` — relation classification
- `fm_save_extract/relation_resolution.py` — typed relation resolution
- `fm_save_extract/diff_decoders.py` — contract/staff diff decoders
- `tests/test_real_slice_extraction.py` — real-slice validation
- `tests/test_real_slice_manifest.py` — slice manifest stability checks
- `STATUS.md` — project-wide current status
- `NEXT_DECODING_BRIEF.md` — next-stage binary decoding priorities
