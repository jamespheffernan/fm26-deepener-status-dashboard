window.STATUS_DATA = {
  "generatedAt": "2026-03-27T14:19:31.088029+00:00",
  "repo": {
    "name": "FM26 Deepener",
    "root": "/Users/jamesheffernan/GitHub/FM26 Deepener"
  },
  "headline": "HTML export parsing remains the practical delivery path today. Save extraction now includes relation tagging, club-link emission, and real-slice validation, but broad live-save coverage is still incomplete. The runtime mod/plugin path is still blocked on macOS Tahoe.",
  "recommendation": "Use the HTML export pipeline for actual content generation now, and treat fm_save_extract as the active automation lane while broadening relation resolution, staff coverage, and real-slice validation.",
  "health": {
    "status": "active",
    "testSuite": {
      "ok": true,
      "count": 49,
      "command": "python3 -m unittest discover -s tests -p test_*.py",
      "output": ".................................................\n----------------------------------------------------------------------\nRan 49 tests in 0.448s\n\nOK"
    },
    "docDriftCount": 0
  },
  "metrics": [
    {
      "label": "Tests",
      "value": "49",
      "detail": "Passing unittest suite"
    },
    {
      "label": "Test Modules",
      "value": "10",
      "detail": "Separate regression suites under tests/"
    },
    {
      "label": "HTML Tests",
      "value": "9",
      "detail": "Parser, snapshot, and prompt-pack coverage"
    },
    {
      "label": "Save Tests",
      "value": "40",
      "detail": "Extractor, relations, hardening, and real-slice coverage"
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
      "label": "Real Slices",
      "value": "6",
      "detail": "Manifest-backed control/edit slices for save extraction"
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
        "9 HTML-focused tests lock the parser, snapshot builder, CLI, and prompt outputs."
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
      "name": "World extractor core",
      "status": "active",
      "stage": "useful, still incomplete",
      "summary": "Binary save work is now a real extraction surface: the CLI emits people, players, staff roles, club links, contracts, and unresolved evidence from live save data.",
      "bullets": [
        "Canonical people, alias keys, inline-name reconciliation, and metadata-backed evidence are wired into the extractor.",
        "Structured bundle outputs exist for club links and contracts, not just raw player candidates.",
        "40 save-related tests now cover extraction, reconciliation, relations, hardening, and real slices."
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
          "label": "Inline people + relations",
          "href": "../fm_save_extract/inline_people.py",
          "path": "fm_save_extract/inline_people.py",
          "exists": "true"
        },
        {
          "label": "Reconciliation tests",
          "href": "../tests/test_extractor_reconciliation.py",
          "path": "tests/test_extractor_reconciliation.py",
          "exists": "true"
        }
      ]
    },
    {
      "name": "Relation decoding and club links",
      "status": "active",
      "stage": "typed and partially resolved",
      "summary": "The extractor now parses inline relation entries, classifies them into typed families, emits club-link records, and resolves supported club-employment patterns.",
      "bullets": [
        "Supported relation families currently include club employment, staff assignment, and contract references.",
        "People can carry typed relation summaries and staff roles can carry typed link refs.",
        "Resolution is improving, but some successful club matches are still pattern-backed rather than generalized."
      ],
      "evidence": [
        {
          "label": "Relation tags",
          "href": "../fm_save_extract/relation_tags.py",
          "path": "fm_save_extract/relation_tags.py",
          "exists": "true"
        },
        {
          "label": "Relation resolution",
          "href": "../fm_save_extract/relation_resolution.py",
          "path": "fm_save_extract/relation_resolution.py",
          "exists": "true"
        },
        {
          "label": "Relation tag tests",
          "href": "../tests/test_relation_tags.py",
          "path": "tests/test_relation_tags.py",
          "exists": "true"
        },
        {
          "label": "Relation resolution tests",
          "href": "../tests/test_relation_resolution.py",
          "path": "tests/test_relation_resolution.py",
          "exists": "true"
        }
      ]
    },
    {
      "name": "Real-slice validation and hardening",
      "status": "verified",
      "stage": "manifest-backed",
      "summary": "The save extractor is no longer validated only by synthetic fixtures: there is now hardening coverage plus a real-slice manifest that locks targeted contract, staff, and control families.",
      "bullets": [
        "6 real slices currently cover Xabi contract edits, Jorge staff-family edits, and an Athletic Club control family.",
        "Diff-decoder hardening covers generic labels and reversed frame order.",
        "This is strong targeted validation, but it still needs to grow across more live families."
      ],
      "evidence": [
        {
          "label": "Real slice builder",
          "href": "../scripts/build_real_slice_fixtures.py",
          "path": "scripts/build_real_slice_fixtures.py",
          "exists": "true"
        },
        {
          "label": "Slice manifest tests",
          "href": "../tests/test_real_slice_manifest.py",
          "path": "tests/test_real_slice_manifest.py",
          "exists": "true"
        },
        {
          "label": "Real slice extraction tests",
          "href": "../tests/test_real_slice_extraction.py",
          "path": "tests/test_real_slice_extraction.py",
          "exists": "true"
        },
        {
          "label": "Diff hardening tests",
          "href": "../tests/test_diff_decoder_hardening.py",
          "path": "tests/test_diff_decoder_hardening.py",
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
      "title": "Broaden relation resolution",
      "detail": "Expand club and employment resolution beyond the current control-pattern-backed cases."
    },
    {
      "title": "Generalize staff families",
      "detail": "Promote targeted staff-role success cases into broader live-save coverage across more manager and coach neighborhoods."
    },
    {
      "title": "Expand contract coverage",
      "detail": "Move from targeted Xabi-style contract families to broader live-save contract extraction with more edited-save controls."
    },
    {
      "title": "Keep adding real slices",
      "detail": "Turn each newly understood family into a manifest-backed real-slice fixture before broadening heuristics further."
    }
  ],
  "blockers": [
    {
      "title": "Runtime injection is blocked on macOS Tahoe",
      "detail": "The BepInEx stack still cannot satisfy the arm64e runtime requirement, so the plugin lane should stay deprioritized."
    },
    {
      "title": "Relation resolution is only partially generalized",
      "detail": "Some successful club-link resolution still depends on known control patterns instead of broad decoding across many clubs and staff families."
    },
    {
      "title": "Binary field layouts can drift with game updates",
      "detail": "The save-decoding track is valuable but fragile, so evidence and confidence need to stay visible in the tracker."
    }
  ],
  "recentChanges": [
    "The test suite has expanded to 49 passing tests across 10 modules.",
    "The extractor now emits canonical people, alias keys, typed relation summaries, and club-link records.",
    "Real-slice manifest and extraction tests now validate targeted contract, staff, and control families."
  ],
  "docDrift": [],
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
      "label": "Reconciliation tests",
      "href": "../tests/test_extractor_reconciliation.py",
      "path": "tests/test_extractor_reconciliation.py",
      "exists": "true"
    },
    {
      "label": "Real slice extraction tests",
      "href": "../tests/test_real_slice_extraction.py",
      "path": "tests/test_real_slice_extraction.py",
      "exists": "true"
    }
  ],
  "refreshCommand": "python3 scripts/build_status_dashboard.py"
};
