// feature.as — one example feature module.
// AS counterpart to templates/full-project/feature.em.
// Demonstrates rule #4 (update/render separation), rule #3 (null checks),
// rule #7 (raw RGBA ints in draw calls), rule #11 (GUI-bound tunables).
//
// In AS the "update" and "render" routines aren't separate the way Enma's
// register_routine() supports — typical pattern is one on_tick callback that
// does both. The discipline is the same: do reads first, draws second, never
// interleaved.

// Cached state — sized once, reused; not allocated per frame.
const int MAX_ENTITIES = 64;
array<uint64> g_cache_addrs(MAX_ENTITIES, 0);    // entity pointers
array<int>    g_cache_team(MAX_ENTITIES, 0);
int           g_cache_count = 0;

void feature_update_and_render() {
    if (g_proc is null || !g_proc.alive()) return;
    if (!g_enabled) return;
    if (g_off_entity_list == 0) return;

    // ── UPDATE: reads + logic, no draws ──
    g_cache_count = 0;
    for (int i = 0; i < MAX_ENTITIES; i++) {
        // 8-byte stride per pointer in the list (uint64 throughout)
        uint64 slot = g_off_entity_list + uint64(i) * 8;
        uint64 ent  = g_proc.ru64(slot);
        if (ent == 0) continue;                  // null gate (rule #3)

        // (Read whatever fields the feature needs — kept generic in this scaffold.
        //  Real templates would dump a struct via read_memory and parse.)
        int team = g_proc.r32(ent + 0xF0);       // <- replace with your offset

        g_cache_addrs[g_cache_count] = ent;
        g_cache_team[g_cache_count]  = team;
        g_cache_count++;
    }

    // ── RENDER: draws only, no reads. ──
    float vw, vh;
    get_view(vw, vh);

    for (int i = 0; i < g_cache_count; i++) {
        // Trivial demo: draw a small marker top-left tagged with the team id.
        // Replace with the real W2S + box draw for your project.
        float x = 10.0f + float(i % 32) * 18.0f;
        float y = 30.0f + float(i / 32) * 22.0f;
        draw_rect_filled(x, y, 14.0f, 14.0f,
                         g_color_r, g_color_g, g_color_b, g_color_a,
                         3.0f, RR_ALL);
    }
}
