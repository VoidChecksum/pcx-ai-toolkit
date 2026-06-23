// main.as — entry point for the AngelScript project scaffold.
// AS counterpart to templates/full-project/main.em.
//
// Differences from the Enma scaffold (see skill://pcx-angelscript-discipline):
//   * int main() returns int (not int64); 1 = stay loaded, 0 = unload.
//   * register_callback(fn, interval_ms, data_index) instead of register_routine.
//   * Callback signature is void on_X(int id, int data_index).
//   * log(...) instead of println(...).
//   * on_unload() releases the proc_t handle via deref() (required, rule #3).
//
// AS scripts are SINGLE FILE at compile time — AngelScript doesn't have an
// `import` statement the way Enma does; everything in this scaffold sits in
// the same script context. The split into globals.as / feature.as / main.as
// is for the HUMAN reader's organization; the AS engine sees one program.
// If your AS host registers a module-bundling step, follow its convention.

int main() {
    // 1. Attach.
    @g_proc = ref_process("game.exe");                // <- set your process name
    if (g_proc is null) {
        log("[main] target process not found");
        return 0;
    }
    if (!g_proc.alive()) {
        log("[main] process handle not alive");
        g_proc.deref();
        @g_proc = null;
        return 0;
    }

    // 2. Resolve module base + size.
    if (!g_proc.get_module("game.exe", g_base, g_size)) {
        log("[main] module base or size 0");
        g_proc.deref();
        @g_proc = null;
        return 0;
    }

    // 3. Resolve offsets via pattern scans.
    //    Replace these with your project's real sigs; mark UNVERIFIED per rule #1.
    uint64 hit_el = g_proc.find_code_pattern(
        g_base, g_size,
        "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8"); // UNVERIFIED
    if (hit_el == 0) {
        log("[main] entity_list sig stale");
        g_proc.deref();
        @g_proc = null;
        return 0;
    }
    int32 disp_el = g_proc.r32(hit_el + 3);
    g_off_entity_list = hit_el + 7 + uint64(disp_el);

    // 4. Register the tick callback (~120 Hz; 8 ms interval).
    //    Signature: void on_tick(int id, int data_index)
    g_cb_tick = register_callback(on_tick, 8, 0);

    g_initialized = true;
    log("[main] loaded");
    return 1;
}

void on_tick(int id, int data_index) {
    feature_update_and_render();
}

void on_unload() {
    // Required per AS discipline rule #3 — deref the handle, unregister callbacks.
    if (g_cb_tick != 0) {
        unregister_callback(g_cb_tick);
        g_cb_tick = 0;
    }
    if (g_proc !is null) {
        g_proc.deref();
        @g_proc = null;
    }
    g_initialized = false;
    log("[main] unloaded");
}
