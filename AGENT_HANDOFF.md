# FM26 Deepener — Agent Handoff Brief

## Goal
Reverse-engineer where FM26 stores player attributes in save files so we can extract structured player data (all 49 attributes + CA/PA + positions) for every player directly from `.fm` saves.

## What's Working
- **Save decompression**: `scripts/decompress_save.py` — .fm → zstd frames → raw binary
- **Name tables extracted**: 291K first names, 596K surnames, 24K clubs → `output/*.json`
- **Date format cracked**: `[uint16 day_of_year][uint16 year]`
- **HTML export pipeline**: `fm_html_extract/` — parses FM's Ctrl+P exports, generates LLM prompt packs. 9 tests passing.
- **Python venv**: `.venv/` with zstandard 0.25.0

## Current Save Files
- **Original (unmodified)**: `frames_claude/frame3.bin` (198.4MB decompressed Frame 3)
- **Modified (Finishing 18→1)**: `frames_claude/frame3_modified.bin` (198.4MB, Haaland's Finishing changed via FMRTE)
- Source save: `"Cesar Jules - Grenoble (v03) - CLAUDE.fm"` in `~/Library/Application Support/Sports Interactive/Football Manager 26/games/`

## Haaland's Known Data (from FMRTE, exact true values)
```
Unique ID: 29179241 (0x01BD3D69)
CA: 195, PA: 195
Height: 195cm, Born: 7/21/2000
Left Foot: 20, Right Foot: 11

Technical: Cor=7, Cro=11, Dri=14, Fin=18(→1 in modified), FT=15, FK=15, Hea=16, LS=13, LT=5, Mar=8, Pas=13, Pen=17, Tac=8, Tec=15
Mental: Agg=15, Ant=20, Bra=15, Com=18, Con=15, Dec=16, Det=20, Fla=16, Lea=14, OTB=19, Pos=9, TW=14, Vis=15, WR=13
Physical: Acc=17, Agi=17, Bal=18, Jum=19, NF=19, Pac=19, Sta=14, Str=17
Hidden: Consistency=18, Dirtiness=9, ImpMatches=14, Versatility=11, InjProneness=10
Personality: Ada=16, Amb=20, Loy=15, Pre=18, Pro=17, Spo=10, Tem=12, Ctv=11
Reputation: Home=8904, Current=9459, World=10000
```

## What We've Located in frame3.bin

| Data | Offset (original) | Offset (modified) | Status |
|------|-------------------|-------------------|--------|
| Reputation (Home+Cur+World, 6 contiguous bytes) | 0x060de435 | 0x060de19d | CONFIRMED |
| **Personality (8 contiguous bytes)** | **0x060de958** | — | **CONFIRMED** (exact match) |
| Unique ID (uint32 LE) | 0x060deb6e | 0x060de8d6 | CONFIRMED |
| Surname ID "12 a3 06" in attr region | 0x0759f4fc | 0x0759f054 | Found but NO attr diffs here |
| Surname table (260K entries) | ~0x04F27A9B | — | Parsed |
| First name table (291K entries) | ~0x045ECA59 | — | Parsed |

## What We Know About Storage Architecture
1. **Player data is split across multiple sections.** UID, reputation, personality, surname ID references, and attributes are NOT co-located. They're in separate serialized pools.
2. **Personality IS stored as 8 contiguous bytes** at 0x060de958 (534 bytes before UID). Order: Adaptability, Ambition, Loyalty, Pressure, Professionalism, Sportsmanship, Temperament, Controversy.
3. **Technical/Mental/Physical attributes are NOT stored as contiguous byte blocks.** Zero hits for any 5+ byte contiguous sequence in any order we tried (alphabetical, game display, FMScoutFramework). They're stored differently — possibly with per-attribute type tags, or in a different frame, or with some encoding.
4. **Diffing original vs modified save**: The files differ by 1352 bytes in size and ~153M bytes total (game re-serializes everything). But UID/reputation/personality regions showed 0 local diffs, meaning the Finishing change is in a DIFFERENT section entirely.
5. **The bytes near surname ID (0x0759f4fc)** contain values like `53 00 58 00 22 04 23 04...` followed by small values (22,12,6,5,8,17,13,11,14,9,8,15,10,2,14...) — these are NOT the main player attributes (Finishing=18 is absent). Might be position ratings or some other sub-object.

## Recommended Next Steps (in order)

### A. Find the Finishing change via smarter alignment
The two frame3 files differ in size by 1352 bytes. A naive byte diff won't work. Instead:
1. Use the UID as an anchor to align the two files
2. Walk outward from the UID in both files, looking for matching structural markers
3. When you find a region where the original has 18 and the modified has 1, that's Finishing
4. Alternatively: find long identical byte sequences (anchors) in both files, then compare the gaps between anchors

### B. Search for attributes with gaps/tags
Maybe each attribute is stored as `[tag_byte, value_byte]` or `[uint16_tag, uint8_value]`. Try:
- Search for `XX 12` (tag + Finishing=18) in original vs `XX 01` (tag + Finishing=1) in modified, where XX is the same byte
- Or search for Finishing in a wider attribute record: the FMRTE attribute ID for Finishing might be a specific constant

### C. Use il2cpp metadata
`GameAssembly.dylib` in the FM26 game folder contains il2cpp compiled code. Tools like Il2CppDumper or Il2CppInspector can extract class definitions showing exact field names and types for Player, Person, PlayerStats objects. This would tell us the serialization structure.

### D. Ask the user to do a SECOND FMRTE edit
Change a different attribute (e.g., Pace=19→1) and save to a THIRD file. With two known changes, finding the intersection of differences becomes much more constrained.

## Key Files
- `research/binary-format-findings.md` — comprehensive format documentation
- `research/ce_attribute_offsets.md` — FMScoutFramework offset map (FM14-16, not directly applicable to FM26)
- `scripts/fm26_parser.py` — working parser for names, clubs, game info
- `scripts/find_by_uid.py` — UID/reputation/attribute search tool
- `scripts/match_attributes.py` — attribute alignment testing
- `STATUS.md` — full project status
- `AGENT_HANDOFF.md` — this file
