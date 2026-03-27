using System;
using System.IO;
using BepInEx.Logging;
using UnityEngine;

namespace FM26Deepener;

/// <summary>
/// Placeholder for Phase 3 — actual data export.
/// For now, F11 just logs that it's ready. Once we discover the game's data model
/// classes via TypeDiscovery (Phase 2), we'll fill this in with actual extractors.
/// </summary>
public class DataExporter : MonoBehaviour
{
    private static ManualLogSource Log => Plugin.Log;

    private static readonly string OutputDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        "Library", "Application Support", "Sports Interactive",
        "Football Manager 26", "deepener");

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.F11))
        {
            Log.LogInfo("F11 pressed — data export triggered");
            Export();
        }
    }

    private void Export()
    {
        Directory.CreateDirectory(OutputDir);

        // Phase 3: After type discovery, this will:
        // 1. Find game singleton/manager objects
        // 2. Traverse player/club/match data
        // 3. Serialize to JSON files in OutputDir

        var statusPath = Path.Combine(OutputDir, "export_status.txt");
        var status = $"FM26 Deepener Export\n" +
                     $"Timestamp: {DateTime.Now:O}\n" +
                     $"Status: Awaiting type discovery (run F10 first, then analyze type_catalog.txt)\n" +
                     $"Output dir: {OutputDir}\n";

        File.WriteAllText(statusPath, status);
        Log.LogInfo($"Export status written to {statusPath}");
        Log.LogInfo("Data export not yet implemented — run type discovery (F10) first");
    }
}
