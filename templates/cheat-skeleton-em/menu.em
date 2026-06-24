// menu.em — config, keybinds, save/load
// Host must grant PERM_FILE before compiling this script.
#pragma once

import "globals";
import "json";
import "file";
import "strings";

const string CONFIG_PATH = "cheat_skeleton_config.json";

sidebar_section_t g_sec;
checkbox_t        g_cb_esp;
checkbox_t        g_cb_aim;
slider_t          g_sl_smooth;
slider_t          g_sl_fov;
checkbox_t        g_cb_trigger;
checkbox_t        g_cb_radar;

// on_change callbacks receive the widget handle (int64); we sync globals here.
void on_esp(int64 h)     { g_esp_enabled     = g_cb_esp.get(); }
void on_aim(int64 h)     { g_aim_enabled     = g_cb_aim.get(); }
void on_smooth(int64 h)  { g_aim_smooth      = g_sl_smooth.get(); }
void on_fov(int64 h)     { g_aim_fov         = g_sl_fov.get(); }
void on_trigger(int64 h) { g_trigger_enabled = g_cb_trigger.get(); }
void on_radar(int64 h)   { g_radar_enabled   = g_cb_radar.get(); }
void on_save(int64 h)    { save_config(); }

void setup_menu() {
    load_config();

    g_sec = create_sidebar_section("Cheat Skeleton", "");
    g_sec.create_separator();

    g_cb_esp = g_sec.create_checkbox("ESP", g_esp_enabled);
    g_cb_esp.on_change(cast<int64>(on_esp));
    g_cb_aim = g_sec.create_checkbox("Aimbot", g_aim_enabled);
    g_cb_aim.on_change(cast<int64>(on_aim));

    g_sl_smooth = g_sec.create_slider("Aim Smooth", g_aim_smooth, 0.01, 1.0, 0.01);
    g_sl_smooth.on_change(cast<int64>(on_smooth));
    g_sl_fov = g_sec.create_slider("Aim FOV", g_aim_fov, 1.0, 180.0, 1.0);
    g_sl_fov.on_change(cast<int64>(on_fov));

    g_cb_trigger = g_sec.create_checkbox("Trigger", g_trigger_enabled);
    g_cb_trigger.on_change(cast<int64>(on_trigger));
    g_cb_radar = g_sec.create_checkbox("Radar", g_radar_enabled);
    g_cb_radar.on_change(cast<int64>(on_radar));

    g_sec.create_separator();
    button_t save_btn = g_sec.create_button("Save Config", ui_align::right);
    save_btn.on_change(cast<int64>(on_save));
}

void save_config() {
    json_value root = json_object();
    root.set_key("esp_enabled",     json_parse(g_esp_enabled     ? "true" : "false"));
    root.set_key("aim_enabled",     json_parse(g_aim_enabled     ? "true" : "false"));
    root.set_key("aim_smooth",      json_parse(format("{f}", g_aim_smooth)));
    root.set_key("aim_fov",         json_parse(format("{f}", g_aim_fov)));
    root.set_key("trigger_enabled", json_parse(g_trigger_enabled ? "true" : "false"));
    root.set_key("radar_enabled",   json_parse(g_radar_enabled   ? "true" : "false"));

    fs_write_file(CONFIG_PATH, root.pretty());
}

void load_config() {
    if (!fs_file_exists(CONFIG_PATH)) return;
    string text = fs_read_file(CONFIG_PATH);
    json_value root = json_parse(text);
    if (!root.is_obj()) return;

    json_value v;
    v = root.get_key("esp_enabled");     if (v.is_bool()) g_esp_enabled     = v.as_bool();
    v = root.get_key("aim_enabled");     if (v.is_bool()) g_aim_enabled     = v.as_bool();
    v = root.get_key("aim_smooth");      if (v.is_num())  g_aim_smooth      = v.as_num();
    v = root.get_key("aim_fov");         if (v.is_num())  g_aim_fov         = v.as_num();
    v = root.get_key("trigger_enabled"); if (v.is_bool()) g_trigger_enabled = v.as_bool();
    v = root.get_key("radar_enabled");   if (v.is_bool()) g_radar_enabled   = v.as_bool();
}
