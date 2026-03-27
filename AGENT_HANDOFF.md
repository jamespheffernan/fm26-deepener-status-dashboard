# FM26 Deepener — Agent Handoff Brief

## Goal
Take the current first-pass FM26 world extractor from "anchored records with partial joins" to "reliable live-save world state" across players, people, staff roles, contracts, and club links.

## Current Repo State
- **HTML export pipeline is production-ready**
  - `python3 -m fm_html_extract`
  - 9 recognized export types
  - 7 prompt templates plus `snapshot-overview.md`
- **Binary save extraction is no longer just research**
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
  - 20 passing tests total
  - `tests/test_fm_html_extract.py`: 9 tests
  - `tests/test_fm_save_extract.py`: 11 tests

## What's Working
- **Save decompression**: `scripts/decompress_save.py` and `fm_save_extract.binary.decompress_main_frame`
- **Reference data extraction**:
  - 291,128 first names
  - 595,757 surnames
  - 24,098 clubs
  - game date/version/header counts
- **Known hybrid player block decode**
  - 15 position bytes on the `1-20` scale
  - 54 classic FM attributes on internal `0-100` values
  - fixed preamble at `block - 0x1E` for reputation + CA/PA
- **Candidate enumeration**
  - `fm_save_extract.player_blocks.enumerate_person_candidates`
  - confidence scoring and known-player matching
- **Inline named-person extraction**
  - `fm_save_extract.inline_people.extract_inline_named_people`
- **Metadata clustering**
  - `fm_save_extract.metadata`
- **Supervised diff summaries**
  - `summarize_diff_frames`
  - `summarize_pairwise_diff_frames`
- **Synthetic decoders already validated**
  - contract wage / expiry
  - staff `WorkingWithYoungsters`

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
  - hybrid-block candidates above confidence threshold
  - inline full-name / DOB people when available
- **Players**
  - positions
  - raw attribute values
  - display attribute values
- **Unresolved evidence**
  - metadata clusters
  - low-confidence people
  - inline-name counts/samples
  - diff summaries when comparison frames are supplied

## What Is Still Missing / Unstable
1. **Club/person/employment joins are incomplete**
- `club_links.json` is a target output surface, but not a stable decoded layer yet.

2. **Staff-side attribute families need better live anchors**
- The extractor has synthetic staff-role validation, but not a generalized live-save staff decoder.

3. **Contract decoding needs real-save generalization**
- Wage / expiry extraction works in supervised synthetic diff tests, but not yet as a broad live-save decoder.

4. **News / inbox / media should wait**
- Those object families depend on reliable joins underneath.

5. **BepInEx remains blocked on Tahoe arm64e**
- Runtime injection experiments are not the shortest path right now.

## Recommended Next Steps

### 1. Generalize person scanning
- Push beyond known-player anchors.
- Build denser candidate enumeration and evidence emission around person pools.

### 2. Stabilize staff-side decoding
- Find manager / assistant / coach candidates using DOB, reputation, and metadata signals.
- Promote role flags and staff attributes beyond the current synthetic-only proof points.

### 3. Map joins
- For each person candidate, find stable nearby refs for:
  - club ids
  - job / role refs
  - team refs
  - contract refs

### 4. Promote contract decoding from synthetic to live-save validated
- Best new edited saves:
  - manager wage change
  - contract expiry change
  - assistant attribute change

### 5. Leave news/media until joins are trustworthy
- Narrative objects are downstream of club/person/competition linkage.

## Key Files
- `fm_save_extract/__main__.py` — world extractor CLI
- `fm_save_extract/extractor.py` — first-pass world-state assembly
- `fm_save_extract/player_blocks.py` — hybrid block decode + candidate enumeration
- `fm_save_extract/diff_decoders.py` — contract/staff diff decoders
- `scripts/fm26_parser.py` — reference extractor for names/clubs/game info
- `research/binary-format-findings.md` — save-format findings
- `STATUS.md` — project-wide current status
- `NEXT_DECODING_BRIEF.md` — next-stage binary decoding priorities
