# Next Decoding Brief

## Current Baseline
- The known hybrid player block is confirmed:
  - `0x00-0x0E`: 15 position ratings on the `1-20` scale
  - `0x0F-0x44`: 54 classic FM attributes on an internal `0-100` scale
- The fixed preamble at `block - 0x1E` is confirmed:
  - Home Reputation
  - Current Reputation
  - World Reputation
  - CA
  - PA
- Haaland remains the strongest verified live anchor:
  - Original block: `0x060DE453`
  - Modified block: `0x060DE1BB`
  - Finishing byte: raw `91 -> 5`, display `18 -> 1`
- A materially richer world extractor now exists:

```bash
python3 -m fm_save_extract --input <save-or-frame> --output-dir <dir> [--raw] [--diff-frame <frame>]
```

- Current extractor outputs:
  - `game_info.json`
  - `clubs.json`
  - `people.json`
  - `players.json`
  - `staff_roles.json`
  - `club_links.json`
  - `contracts.json`
  - `unresolved_candidates.json`
- Current extractor behavior includes:
  - canonical people + `alias_person_keys`
  - inline relation-entry parsing
  - typed relation summaries
  - club-link emission
  - contract enrichment from club links when possible
- Validation now includes:
  - diff-decoder hardening tests
  - relation-tag tests
  - relation-resolution tests
  - reconciliation tests
  - real-slice manifest tests
  - real-slice extraction tests
- Current repo verification: **49 passing tests**

## Immediate Goal
Move from "targeted working extraction + targeted resolution patterns" to "broader live-save coverage that holds across more clubs, staff families, and contract neighborhoods".

## Best Next Targets

### 1. Broaden club / employment relation resolution
- Expand beyond the current control-pattern-backed resolution.
- Resolve more inline relation-entry families into trustworthy `club_links.json` entries.

### 2. Generalize staff-side decoding
- Decode manager / assistant / coach / scout / physio objects across more live families.
- Reuse person-side anchors where possible:
  - UID
  - DOB
  - personality
  - reputation
  - nearby metadata families
  - inline relation windows

### 3. Generalize contract decoding on real saves
- Move beyond the current targeted contract family.
- Decode more live contract objects with:
  - start date
  - expiry date
  - wage
  - bonuses
  - release clauses
  - optional extensions
  - loan terms / future fees if present

### 4. Grow the real-slice fixture corpus
- Keep control/edit slices manifest-backed.
- Add new real slices whenever a new family is understood so regressions are locked down immediately.

### 5. News / inbox / media after joins
- Do this after people/clubs/contracts are reliable.
- The fully rendered narrative text may also live in `.skc` cache files, so save decoding and cache parsing remain parallel options.

## Why This Order
- The extractor already emits `club_links.json`, `staff_roles.json`, and `contracts.json`, so the next leverage comes from making those surfaces trustworthy across more live families.
- Real-slice coverage now exists, which means new understanding should be converted into locked fixtures instead of staying as loose research notes.
- News / inbox still sits on top of entity joins and should stay downstream.

## Useful Metadata Signals Already Seen
- `Manager`
- `AssistantManager`
- `Coaching`
- `Motivating`
- `PeopleManagement`
- `WorkingWithYoungsters`
- `Contract`
- `ContractReference`
- `NonPlayerAttributeReference`
- `PersonReference`
- `NewsItemReference`
- `PlayerHistoryReference`
- `PlayerInjuryReference`
- `PlayerTransferOfferReference`
- `PressConferenceEditSessionReference`
- `SaveGameReference`

## Concrete Tasks

### 1. Broaden relation-family coverage
- Classify and resolve more relation tags beyond the currently supported club-employment / staff-assignment / contract-reference set.

### 2. Tighten person + relation reconciliation
- Keep candidate scanning general, not known-player only.
- Emit stronger evidence bundles per candidate:
  - block start
  - preamble
  - decoded attrs
  - nearby dates
  - possible ids
  - possible club / contract / role refs

### 3. Expand staff-side fixtures
- Add edited-save or slice-backed coverage for more staff neighborhoods.
- Promote role flags and team/club links beyond the current targeted families.

### 4. Expand contract fixtures
- Capture more edited contract families and validate broader extraction behavior, not just the current Xabi-focused path.

## Suggested Validation Method
- Prefer supervised diffs again.
- Best follow-up edited saves:
  - change a manager contract wage
  - change a contract expiry date
  - change assistant attributes in FMRTE
  - capture new real slices immediately once the affected family is localized

## Deliverable For The Next Phase
A stronger world extractor that emits:
- people with better canonicalization
- players
- broader typed relation summaries
- more trustworthy club links
- more reliable staff roles
- more reliable contracts

News and inbox can follow once those joins are stable.
