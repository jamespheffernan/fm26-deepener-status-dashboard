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
- A first-pass world extractor now exists:

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
- Synthetic validation already exists for:
  - contract wage / expiry decoding
  - staff `WorkingWithYoungsters`
- Current repo verification: **20 passing tests**

## Immediate Goal
Move from "first-pass extractor with anchored records" to "live-save validated joins and broader person/staff/contract coverage".

## Best Next Targets

### 1. Club / person / employment links
- Identify how people are linked to clubs, jobs, and teams.
- Needed for:
  - current manager
  - assistant manager
  - coaching staff
  - squad membership
  - contracts
  - loans / affiliations / responsibilities

### 2. Staff-side attribute layouts
- Decode manager / assistant / coach / scout / physio objects.
- Reuse person-side anchors where possible:
  - UID
  - DOB
  - personality
  - reputation
  - nearby metadata families

### 3. Generalize contract decoding on real saves
- Move past synthetic frames and isolate live contract objects.
- Decode:
  - start date
  - expiry date
  - wage
  - bonuses
  - release clauses
  - optional extensions
  - loan terms / future fees if present

### 4. News / inbox / media after joins
- Do this after people/clubs/contracts are reliable.
- The fully rendered narrative text may also live in `.skc` cache files, so save decoding and cache parsing remain parallel options.

## Why This Order
- Staff + links + contracts are the biggest structured win after players.
- `club_links.json` and `contracts.json` already exist as extractor surfaces, so this is the shortest path to turning partial outputs into trustworthy ones.
- News / inbox sits on top of entity joins and should stay downstream.

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

### 1. Tighten person enumeration
- Keep candidate scanning general, not known-player only.
- Emit stronger evidence bundles per candidate:
  - block start
  - preamble
  - decoded attrs
  - nearby dates
  - possible ids
  - possible club / contract / role refs

### 2. Identify staff-only families
- Look for blocks near known manager / assistant anchors.
- Compare candidates against expected staff attributes:
  - coaching
  - motivating
  - people management
  - working with youngsters

### 3. Promote joins into real `club_links.json`
- For each decoded person block, find stable nearby refs for:
  - club ids
  - role / job refs
  - team refs
  - contract refs

### 4. Generalize contract decoding
- Once link candidates stabilize, isolate one known live contract and validate with edited saves.

## Suggested Validation Method
- Prefer supervised diffs again.
- Best follow-up edited saves:
  - change a manager contract wage
  - change a contract expiry date
  - change assistant attributes in FMRTE

## Deliverable For The Next Phase
A stronger world extractor that emits:
- people
- players
- staff roles with better live anchors
- real club links
- more reliable contracts

News and inbox can follow once those joins are stable.
