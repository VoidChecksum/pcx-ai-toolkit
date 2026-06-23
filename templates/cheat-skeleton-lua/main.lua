-- main.lua — entry point and frame hook

require("globals")
require("offsets")
require("utils")
require("esp")
require("aim")
require("triggerbot")
require("radar")
require("menu")

TARGET_PROCESS = "game.exe"  -- REPLACE WITH REAL TARGET

function main()
    g_proc = ref_process(TARGET_PROCESS)
    if not g_proc then
        log("[main] target not found: " .. TARGET_PROCESS)
        return 0
    end

    if not g_proc:alive() then
        log("[main] target not alive: " .. TARGET_PROCESS)
        return 0
    end

    g_base = g_proc:base_address()
    local ok, size = g_proc:get_module(TARGET_PROCESS)
    if not ok or g_base == 0 then
        log("[main] module not ready")
        return 0
    end
    g_size = size

    if not resolve_all() then
        log("[main] signature resolution failed")
        return 0
    end

    g_initialized = true
    setup_menu()

    log("[main] cheat skeleton loaded")
    return 1
end

function on_frame()
    if not g_initialized or not g_proc or not g_proc:alive() then return end

    sync_from_widgets()  -- pull GUI widget state into the config globals

    esp_update()
    aimbot_update()
    triggerbot_update()

    esp_render()
    aimbot_render()
    triggerbot_render()
    radar_render()
end

function on_unload()
    if g_proc then
        deref_process(g_proc)
        g_proc = nil
    end
end
