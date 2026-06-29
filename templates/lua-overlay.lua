local TARGET_PROCESS = "game.exe"
local g_process = nil

function on_frame()
    local w, h = get_view()
    local font = get_font20()

    draw_rect_filled(20, 20, 300, 88, 20, 20, 20, 210, 8.0, RR_TOP_LEFT)
    draw_text("PCX Lua active", 36, 46, 255, 255, 255, 255, font, TE_SHADOW, 0, 0, 0, 180, 1.0)

    if g_process and g_process:alive() then
        draw_text(TARGET_PROCESS, 36, 68, 140, 220, 255, 255, font, TE_NONE, 0, 0, 0, 0, 1.0)
    end
end

function main()
    g_process = ref_process(TARGET_PROCESS)
    log("PCX Lua overlay loaded")
    return 1
end

function on_unload()
    if g_process then
        deref_process(g_process)
        g_process = nil
    end
end
