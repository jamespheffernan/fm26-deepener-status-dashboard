# Next Decoding Brief

## Current Breakthrough
- The real player stats block is now confirmed.
- Layout:
  - `0x00-0x0E`: 15 position ratings stored directly on the `1-20` scale
  - `0x0F-0x44`: 54 classic FM attributes in FMScout/CE order, stored on an internal `0-100` scale
- Display approximation for non-position attributes:
  - `display ~= round(raw / 5)`
- Haaland is confirmed at:
  - Original block: `0x060DE453`
  - Modified block: `0x060DE1BB`
  - Finishing byte: `block + 0x11`, raw `91 -> 5`, display `18 -> 1`
- Fixed preamble at `block - 0x1E`:
  - `+0x00`: Home Reputation (`uint16`)
  - `+0x02`: Current Reputation (`uint16`)
  - `+0x04`: World Reputation (`uint16`)
  - `+0x06`: CA (`uint16`)
  - `+0x08`: PA (`uint16`)

## Immediate Goal
Move from “can decode one known player” to “can extract whole world state”.

## Best Next Targets
1. Staff/person records
- Decode managers, assistants, coaches, scouts, physios.
- Find the non-player/staff attribute block and role flags.
- Reuse the same person-side anchors where possible: UID, DOB, personality, reputation.

2. Club/person/employment links
- Identify how people are linked to clubs and jobs.
- Needed for:
  - current manager
  - assistant manager
  - coaching staff
  - squad membership
  - loans / affiliations / responsibilities

3. Contracts
- Find contract objects and their links to person + club.
- Decode:
  - start date
  - expiry date
  - wage
  - bonuses
  - release clauses
  - optional extension terms
  - loan terms / future fees if present

4. News / inbox / media
- Do this after joins work.
- Likely separate object families with refs to person/team/competition/news type.
- The fully rendered narrative text may also live in `.skc` cache files, so treat save decoding and cache parsing as parallel options.

## Why This Order
- Staff + contracts give the biggest structured win after players.
- News/inbox depends on entity joins underneath it.
- Without club/person/contract linking, decoded records are isolated blobs.

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
1. Generalize block enumeration
- Stop relying on “known player” scanning only.
- Build a scanner that walks candidate person pools and emits blocks with:
  - block start
  - preamble fields
  - decoded attrs
  - nearby dates / ids / possible references

2. Identify staff-only attribute layout
- Look for blocks near known manager/assistant DOBs and reputations.
- Compare candidates against expected staff attributes:
  - coaching
  - motivating
  - people management
  - working with youngsters

3. Map links
- For each decoded person block, find nearby stable refs:
  - club ids
  - contract refs
  - role/job refs
  - team refs

4. Contract decoder
- Once link candidates are stable, isolate one known contract and diff against a changed save if needed.

## Suggested Validation Method
- Prefer supervised diffs again.
- Best follow-up edited saves:
  - change a manager contract wage
  - change a contract expiry date
  - change assistant attributes in FMRTE
- Those will constrain the right object families quickly.

## Deliverable For The Next Phase
A first-pass world extractor that emits:
- people
- players
- staff roles
- club links
- contracts

News and inbox can follow once those joins are stable.
