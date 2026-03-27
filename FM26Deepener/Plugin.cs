using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using UnityEngine;
using Il2CppInterop.Runtime.Injection;

namespace FM26Deepener;

[BepInPlugin(MyPluginInfo.PLUGIN_GUID, MyPluginInfo.PLUGIN_NAME, MyPluginInfo.PLUGIN_VERSION)]
public class Plugin : BasePlugin
{
    internal new static ManualLogSource Log;

    public override void Load()
    {
        Log = base.Log;
        Log.LogInfo($"FM26 Deepener v{MyPluginInfo.PLUGIN_VERSION} loaded");

        try
        {
            ClassInjector.RegisterTypeInIl2Cpp<TypeDiscovery>();
            ClassInjector.RegisterTypeInIl2Cpp<DataExporter>();
        }
        catch (System.Exception ex)
        {
            Log.LogError($"Failed to register types: {ex}");
            return;
        }

        try
        {
            var go = new GameObject("FM26Deepener");
            Object.DontDestroyOnLoad(go);
            go.AddComponent<TypeDiscovery>();
            go.AddComponent<DataExporter>();
            Log.LogInfo("Components attached. Press F10 to dump type catalog, F11 to export data.");
        }
        catch (System.Exception ex)
        {
            Log.LogError($"Failed to create GameObject: {ex}");
        }
    }
}
