// menu.as — config, keybinds, save/load
namespace Cheat {

const string CONFIG_PATH = "cheat_skeleton_config.json";

// Widget handles — widget state is polled back into the globals each tick
// (AngelScript checkboxes/sliders expose get(), not on_change callbacks).
checkbox_t      g_cb_esp;
checkbox_t      g_cb_aim;
slider_double_t g_sl_smooth;
slider_double_t g_sl_fov;
checkbox_t      g_cb_trigger;
checkbox_t      g_cb_radar;

void sync_from_widgets(int id, int data_index) {
    g_esp_enabled     = g_cb_esp.get();
    g_aim_enabled     = g_cb_aim.get();
    g_aim_smooth      = g_sl_smooth.get();
    g_aim_fov         = g_sl_fov.get();
    g_trigger_enabled = g_cb_trigger.get();
    g_radar_enabled   = g_cb_radar.get();
}

void setup_menu() {
    load_config();

    subtab_t st = create_subtab(0, "Cheat Skeleton");
    if (!st.is_valid()) {
        log("[menu] failed to create subtab");
        return;
    }
    panel_t p = st.add_panel("Features", false);

    g_cb_esp     = p.add_checkbox("ESP",      g_esp_enabled);
    g_cb_aim     = p.add_checkbox("Aimbot",   g_aim_enabled);
    g_sl_smooth  = p.add_slider_double("Aim Smooth", "", g_aim_smooth, 0.01, 1.0, 0.01);
    g_sl_fov     = p.add_slider_double("Aim FOV",    "", g_aim_fov,    1.0,  180.0, 1.0);
    g_cb_trigger = p.add_checkbox("Trigger",  g_trigger_enabled);
    g_cb_radar   = p.add_checkbox("Radar",    g_radar_enabled);
    p.add_button("Save Config", @save_config);
}

void save_config() {
    dictionary d;
    d.set("esp_enabled",     g_esp_enabled);
    d.set("aim_enabled",     g_aim_enabled);
    d.set("aim_smooth",      g_aim_smooth);
    d.set("aim_fov",         g_aim_fov);
    d.set("trigger_enabled", g_trigger_enabled);
    d.set("radar_enabled",   g_radar_enabled);

    string json;
    string err;
    if (!json_stringify(d, json, err)) {
        log("[menu] stringify failed: " + err);
        return;
    }
    create_file(CONFIG_PATH, json);
}

void load_config() {
    if (!does_file_exist(CONFIG_PATH)) return;
    string text;
    if (!read_file(CONFIG_PATH, text)) return;

    dictionary d;
    string err;
    if (!json_parse(text, d, err)) {
        log("[menu] parse failed: " + err);
        return;
    }

    // JSON booleans/numbers parse back as double (1.0/0.0 for bools).
    double v;
    if (d.get("esp_enabled",     v)) g_esp_enabled     = (v != 0.0);
    if (d.get("aim_enabled",     v)) g_aim_enabled     = (v != 0.0);
    if (d.get("aim_smooth",      v)) g_aim_smooth      = v;
    if (d.get("aim_fov",         v)) g_aim_fov         = v;
    if (d.get("trigger_enabled", v)) g_trigger_enabled = (v != 0.0);
    if (d.get("radar_enabled",   v)) g_radar_enabled   = (v != 0.0);
}

}
