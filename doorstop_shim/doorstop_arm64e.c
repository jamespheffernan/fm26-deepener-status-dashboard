/*
 * Minimal arm64e doorstop shim for BepInEx on macOS Tahoe (26+).
 *
 * macOS 26 enforces arm64e for DYLD_INSERT_LIBRARIES. The stock
 * BepInEx doorstop only ships arm64/x86_64 slices, so it can't inject.
 *
 * This shim:
 * 1. Runs as a constructor when DYLD loads it into the process
 * 2. Loads the real libdoorstop.dylib via dlopen (which works because
 *    dlopen'd libraries don't need to match the host's arm64e ABI —
 *    only DYLD_INSERT_LIBRARIES entries do)
 * 3. The real doorstop's constructor fires, bootstrapping BepInEx
 *
 * Build: clang -shared -arch arm64e -o libdoorstop_shim.dylib doorstop_arm64e.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <mach-o/dyld.h>

__attribute__((constructor))
static void doorstop_shim_init(void) {
    // Find the game's base directory from the main executable path
    const char *exe_path = _dyld_get_image_name(0);
    if (!exe_path) {
        fprintf(stderr, "[doorstop_shim] Could not determine executable path\n");
        return;
    }

    // Navigate up to the game root: .app/Contents/MacOS/exe -> .app -> game root
    char base_dir[4096];
    strncpy(base_dir, exe_path, sizeof(base_dir) - 1);
    base_dir[sizeof(base_dir) - 1] = '\0';

    // Strip executable name
    char *last_slash = strrchr(base_dir, '/');
    if (last_slash) *last_slash = '\0';
    // Strip MacOS
    last_slash = strrchr(base_dir, '/');
    if (last_slash) *last_slash = '\0';
    // Strip Contents
    last_slash = strrchr(base_dir, '/');
    if (last_slash) *last_slash = '\0';
    // Strip .app name
    last_slash = strrchr(base_dir, '/');
    if (last_slash) *last_slash = '\0';

    fprintf(stderr, "[doorstop_shim] Game root: %s\n", base_dir);

    // Load the real doorstop library via dlopen
    // dlopen'd libraries don't require arm64e matching
    char doorstop_path[4096];
    snprintf(doorstop_path, sizeof(doorstop_path), "%s/libdoorstop.dylib", base_dir);

    fprintf(stderr, "[doorstop_shim] Loading real doorstop: %s\n", doorstop_path);

    void *handle = dlopen(doorstop_path, RTLD_NOW);
    if (!handle) {
        fprintf(stderr, "[doorstop_shim] Failed to load doorstop: %s\n", dlerror());
        fprintf(stderr, "[doorstop_shim] BepInEx will NOT be active this session.\n");
        return;
    }

    fprintf(stderr, "[doorstop_shim] Doorstop loaded successfully. BepInEx should initialize.\n");
    // The real doorstop's __attribute__((constructor)) will have already fired
    // during dlopen, bootstrapping BepInEx's CoreCLR.
}
