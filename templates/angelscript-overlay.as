const string TARGET_PROCESS = "game.exe";

proc_t g_process;

void on_tick(int id, int data_index)
{
    float w, h;
    get_view(w, h);

    uint64 font = get_font20();
    draw_rect_filled(20, 20, 300, 88,
                     20, 20, 20, 210,
                     8.0f, RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT);
    draw_text("PCX AngelScript active",
              36, 46,
              255, 255, 255, 255,
              font,
              TE_SHADOW,
              0, 0, 0, 180,
              1.0f);

    if (g_process.pid() != 0 && g_process.alive())
    {
        draw_text(TARGET_PROCESS,
                  36, 68,
                  140, 220, 255, 255,
                  font,
                  TE_NONE,
                  0, 0, 0, 0,
                  1.0f);
    }
}

int main()
{
    log("AngelScript overlay loaded");
    g_process = ref_process(TARGET_PROCESS);
    register_callback(on_tick, 16, 0);
    return 1;
}

void on_unload()
{
    if (g_process.pid() != 0)
    {
        g_process.deref();
    }
    log("AngelScript overlay unloaded");
}
