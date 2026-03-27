window.STATUS_DATA = {
  "generatedAt": "2026-03-27T12:45:21.767964+00:00",
  "repo": {
    "name": "FM26 Deepener",
    "root": "/Users/jamesheffernan/GitHub/FM26 Deepener"
  },
  "headline": "HTML export parsing is the practical delivery path today. Binary save extraction has advanced into a first-pass world-state toolchain. The runtime mod/plugin path is still blocked on macOS Tahoe.",
  "recommendation": "Use the HTML export pipeline for actual content generation now, and treat save decoding as the parallel R&D track that is steadily becoming more structured.",
  "health": {
    "status": "active",
    "testSuite": {
      "ok": true,
      "count": 19,
      "command": "python3 -m unittest discover -s tests -p test_*.py",
      "output": "...................\n----------------------------------------------------------------------\nRan 19 tests in 0.408s\n\nOK"
    },
    "docDriftCount": 4
  },
  "metrics": [
    {
      "label": "Tests",
      "value": "19",
      "detail": "Passing unittest suite"
    },
    {
      "label": "Export Types",
      "value": "9",
      "detail": "Classified in fm_html_extract.types.ExportType"
    },
    {
      "label": "Prompt Templates",
      "value": "7",
      "detail": "Generated from combined HTML snapshots"
    },
    {
      "label": "Fixture HTMLs",
      "value": "8",
      "detail": "Regression fixtures in tests/fixtures"
    },
    {
      "label": "First Names",
      "value": "291,128",
      "detail": "Reference rows extracted from save data"
    },
    {
      "label": "Surnames",
      "value": "595,757",
      "detail": "Reference rows extracted from save data"
    },
    {
      "label": "Clubs",
      "value": "24,098",
      "detail": "Club names already extracted"
    }
  ],
  "workstreams": [
    {
      "name": "HTML export pipeline",
      "status": "verified",
      "stage": "usable now",
      "summary": "The safest path today: parse FM print exports, assemble multi-export snapshots, and generate prompt packs without touching the game runtime.",
      "bullets": [
        "9 export types are classified in code, including transfers, staff, schedule, competition stats, and news.",
        "7 prompt templates are generated from a combined snapshot.",
        "CLI coverage is verified by the unittest suite, so this is the track to use for real output today."
      ],
      "evidence": [
        {
          "label": "HTML CLI",
          "href": "../fm_html_extract/__main__.py",
          "path": "fm_html_extract/__main__.py",
          "exists": "true"
        },
        {
          "label": "Snapshot builder",
          "href": "../fm_html_extract/snapshot.py",
          "path": "fm_html_extract/snapshot.py",
          "exists": "true"
        },
        {
          "label": "HTML tests",
          "href": "../tests/test_fm_html_extract.py",
          "path": "tests/test_fm_html_extract.py",
          "exists": "true"
        }
      ]
    },
    {
      "name": "First-pass world extractor",
      "status": "active",
      "stage": "real but incomplete",
      "summary": "Binary save work has moved past raw research: there is now a world-state extractor CLI that emits people, players, contracts, staff roles, clubs, and unresolved clues.",
      "bullets": [
        "Main-frame decompression and bundle writing are wired through fm_save_extract.",
        "The extractor emits structured JSON outputs even when some joins are still unresolved.",
        "This is ahead of the current STATUS.md narrative and deserves to be treated as active implementation, not just research."
      ],
      "evidence": [
        {
          "label": "World extractor CLI",
          "href": "../fm_save_extract/__main__.py",
          "path": "fm_save_extract/__main__.py",
          "exists": "true"
        },
        {
          "label": "World extractor",
          "href": "../fm_save_extract/extractor.py",
          "path": "fm_save_extract/extractor.py",
          "exists": "true"
        },
        {
          "label": "Bundle models",
          "href": "../fm_save_extract/models.py",
          "path": "fm_save_extract/models.py",
          "exists": "true"
        },
        {
          "label": "Save extractor tests",
          "href": "../tests/test_fm_save_extract.py",
          "path": "tests/test_fm_save_extract.py",
          "exists": "true"
        }
      ]
    },
    {
      "name": "Known-player block decoding",
      "status": "active",
      "stage": "anchored on verified cases",
      "summary": "The hybrid player block is pinned down well enough to decode positions, the visible attribute family, and the CA/PA reputation preamble for known records.",
      "bullets": [
        "Haaland remains the strongest verified anchor for byte-level decoding and diff validation.",
        "The extractor can enumerate candidate people from hybrid blocks and score known matches.",
        "The remaining gap is scaling from anchored records to robust whole-world joins."
      ],
      "evidence": [
        {
          "label": "Player block decoder",
          "href": "../fm_save_extract/player_blocks.py",
          "path": "fm_save_extract/player_blocks.py",
          "exists": "true"
        },
        {
          "label": "Agent handoff",
          "href": "../AGENT_HANDOFF.md",
          "path": "AGENT_HANDOFF.md",
          "exists": "true"
        },
        {
          "label": "Next decoding brief",
          "href": "../NEXT_DECODING_BRIEF.md",
          "path": "NEXT_DECODING_BRIEF.md",
          "exists": "true"
        }
      ]
    },
    {
      "name": "Diff-assisted contracts and staff roles",
      "status": "partial",
      "stage": "promising, synthetic-only",
      "summary": "There is real decoder logic for contracts and staff roles, but the current confidence comes from supervised synthetic frames rather than broad live-save coverage.",
      "bullets": [
        "Contract wage and expiry decoding are validated in unit tests.",
        "Staff role decoding already isolates Working With Youngsters in a supervised diff family.",
        "This track is worth surfacing, but not yet something to oversell as production-ready."
      ],
      "evidence": [
        {
          "label": "Diff decoders",
          "href": "../fm_save_extract/diff_decoders.py",
          "path": "fm_save_extract/diff_decoders.py",
          "exists": "true"
        },
        {
          "label": "Diff decoder tests",
          "href": "../tests/test_fm_save_extract.py",
          "path": "tests/test_fm_save_extract.py",
          "exists": "true"
        }
      ]
    },
    {
      "name": "BepInEx runtime plugin",
      "status": "blocked",
      "stage": "waiting on upstream/runtime",
      "summary": "The plugin scaffolding exists, but the macOS Tahoe arm64e barrier still blocks the injected runtime path.",
      "bullets": [
        "The plugin project and deployment script are present.",
        "The arm64e shim work proved injection, but not a usable runtime bridge.",
        "This remains a blocked lane until the native stack catches up."
      ],
      "evidence": [
        {
          "label": "Plugin entry point",
          "href": "../FM26Deepener/Plugin.cs",
          "path": "FM26Deepener/Plugin.cs",
          "exists": "true"
        },
        {
          "label": "Exporter stub",
          "href": "../FM26Deepener/DataExporter.cs",
          "path": "FM26Deepener/DataExporter.cs",
          "exists": "true"
        },
        {
          "label": "arm64e shim",
          "href": "../doorstop_shim/doorstop_arm64e.c",
          "path": "doorstop_shim/doorstop_arm64e.c",
          "exists": "true"
        },
        {
          "label": "Status write-up",
          "href": "../STATUS.md",
          "path": "STATUS.md",
          "exists": "true"
        }
      ]
    }
  ],
  "currentFocus": [
    {
      "title": "Generalize person scanning",
      "detail": "Move from one anchored player to a scanner that enumerates candidate person blocks and emits structured evidence at scale."
    },
    {
      "title": "Decode staff-side layouts",
      "detail": "Use known managers and assistants to stabilize the non-player/staff attribute family."
    },
    {
      "title": "Map links and contracts",
      "detail": "Connect people to clubs, roles, and contracts so the extracted records stop being isolated blobs."
    },
    {
      "title": "Push news and inbox later",
      "detail": "Treat narrative/media extraction as a second phase after person-club-contract joins are trustworthy."
    }
  ],
  "blockers": [
    {
      "title": "Runtime injection is blocked on macOS Tahoe",
      "detail": "The BepInEx stack still cannot satisfy the arm64e runtime requirement, so the plugin lane should stay deprioritized."
    },
    {
      "title": "Status docs lag the repo",
      "detail": "The markdown briefs are directionally right, but they now understate test coverage and the fm_save_extract implementation surface."
    },
    {
      "title": "Binary field layouts can drift with game updates",
      "detail": "The save-decoding track is valuable but fragile, so evidence and confidence need to stay visible in the tracker."
    }
  ],
  "recentChanges": [
    "The repo now has a dedicated fm_save_extract CLI for first-pass world extraction, not just one-off research scripts.",
    "Synthetic decoding coverage exists for contract changes and staff-role attribute diffs.",
    "The HTML-export lane now covers more export types and more prompt outputs than STATUS.md currently reports."
  ],
  "docDrift": [
    "STATUS.md still tops out at 7 passing tests, while the repo now passes 19.",
    "AGENT_HANDOFF.md still cites 9 passing tests, so the handoff brief is behind the repo.",
    "STATUS.md does not mention the newer fm_save_extract CLI or the first-pass world-state bundle outputs.",
    "The status docs do not yet reflect synthetic coverage for contract decoding and staff-role diff decoding."
  ],
  "sources": [
    {
      "label": "STATUS.md",
      "href": "../STATUS.md",
      "path": "STATUS.md",
      "exists": "true"
    },
    {
      "label": "AGENT_HANDOFF.md",
      "href": "../AGENT_HANDOFF.md",
      "path": "AGENT_HANDOFF.md",
      "exists": "true"
    },
    {
      "label": "NEXT_DECODING_BRIEF.md",
      "href": "../NEXT_DECODING_BRIEF.md",
      "path": "NEXT_DECODING_BRIEF.md",
      "exists": "true"
    },
    {
      "label": "HTML pipeline tests",
      "href": "../tests/test_fm_html_extract.py",
      "path": "tests/test_fm_html_extract.py",
      "exists": "true"
    },
    {
      "label": "Save extractor tests",
      "href": "../tests/test_fm_save_extract.py",
      "path": "tests/test_fm_save_extract.py",
      "exists": "true"
    }
  ],
  "refreshCommand": "python3 scripts/build_status_dashboard.py"
};
