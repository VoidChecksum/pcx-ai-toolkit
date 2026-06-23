-- menu.lua — config, keybinds, save/load

CONFIG_PATH = "cheat_skeleton_config.json"

-- Widget handles — widget state is polled back into the config globals each
-- frame (Lua checkboxes/sliders expose :get(), not on_change callbacks).
g_cb_esp     = nil
g_cb_aim     = nil
g_sl_smooth  = nil
g_sl_fov     = nil
g_cb_trigger = nil
g_cb_radar   = nil

function sync_from_widgets()
    if g_cb_esp     then g_esp_enabled     = g_cb_esp:get()     end
    if g_cb_aim     then g_aim_enabled     = g_cb_aim:get()     end
    if g_sl_smooth  then g_aim_smooth      = g_sl_smooth:get()  end
    if g_sl_fov     then g_aim_fov         = g_sl_fov:get()     end
    if g_cb_trigger then g_trigger_enabled = g_cb_trigger:get() end
    if g_cb_radar   then g_radar_enabled   = g_cb_radar:get()   end
end

function setup_menu()
    load_config()

    local st = ui.create_subtab(0, "Cheat Skeleton")
    local p  = st:add_panel("Features", false)

    g_cb_esp     = p:add_checkbox("ESP",      g_esp_enabled)
    g_cb_aim     = p:add_checkbox("Aimbot",   g_aim_enabled)
    g_sl_smooth  = p:add_slider_double("Aim Smooth", "", g_aim_smooth, 0.01, 1.0, 0.01)
    g_sl_fov     = p:add_slider_double("Aim FOV",    "", g_aim_fov,    1.0,  180.0, 1.0)
    g_cb_trigger = p:add_checkbox("Trigger",  g_trigger_enabled)
    g_cb_radar   = p:add_checkbox("Radar",    g_radar_enabled)
    p:add_button("Save Config", save_config)
end

function save_config()
    local t = {
        esp_enabled     = g_esp_enabled,
        aim_enabled     = g_aim_enabled,
        aim_smooth      = g_aim_smooth,
        aim_fov         = g_aim_fov,
        trigger_enabled = g_trigger_enabled,
        radar_enabled   = g_radar_enabled,
    }
    local json, err = json.stringify(t)
    if not json then
        log("[menu] stringify failed: " .. tostring(err))
        return
    end
    create_file(CONFIG_PATH, json)
end

function load_config()
    if not does_file_exist(CONFIG_PATH) then return end
    local ok, text = read_file(CONFIG_PATH)
    if not ok then return end

    local root, err = json.parse(text)
    if not root or type(root) ~= "table" then return end

    -- json.parse returns native Lua types (boolean/number), so type-guard each field.
    if type(root.esp_enabled)     == "boolean" then g_esp_enabled     = root.esp_enabled     end
    if type(root.aim_enabled)     == "boolean" then g_aim_enabled     = root.aim_enabled     end
    if type(root.aim_smooth)      == "number"  then g_aim_smooth      = root.aim_smooth      end
    if type(root.aim_fov)         == "number"  then g_aim_fov         = root.aim_fov         end
    if type(root.trigger_enabled) == "boolean" then g_trigger_enabled = root.trigger_enabled end
    if type(root.radar_enabled)   == "boolean" then g_radar_enabled   = root.radar_enabled   end
end