// menu.em — GUI sidebar + config persistence.
// Every tunable is a widget; config saves/loads via the filesystem API.

// Host must grant PERM_FILE before compiling this script.

import "color";
import "file";
import "globals";
import "strings";

sidebar_section_t g_sec;
checkbox_t        g_cb_enabled;
slider_t          g_sl_dist;
colorpicker_t     g_cp_color;

void on_enabled(int64 h) { g_enabled      = g_cb_enabled.get(); }
void on_dist(int64 h)    { g_max_distance = g_sl_dist.get(); }
void on_color(int64 h)   { g_color        = g_cp_color.get(); }
void on_save(int64 h)    { save_config(); }

void save_config() {
    string cfg = "";
    cfg = cfg + "enabled="  + cast<string>(g_enabled) + "\n";
    cfg = cfg + "max_dist=" + cast<string>(g_max_distance) + "\n";
    fs_write_file("config.txt", cfg);
}

void load_config() {
    if (!fs_file_exists("config.txt")) return;
    string cfg = fs_read_file("config.txt");
    for (string line : cfg.split("\n")) {
        array<string> kv = line.split("=");
        if (kv.length() < 2) continue;
        if (kv[0] == "enabled")  g_enabled = (kv[1] == "true" || kv[1] == "1");
        if (kv[0] == "max_dist") g_max_distance = kv[1].to_float();
    }
}

void setup_menu() {
    load_config();
    g_sec = create_sidebar_section("Project", "");
    g_cb_enabled = g_sec.create_checkbox("Enabled", g_enabled);
    g_cb_enabled.on_change(cast<int64>(on_enabled));
    g_sl_dist = g_sec.create_slider("Max Distance", g_max_distance, 0.0, 10000.0, 1.0);
    g_sl_dist.on_change(cast<int64>(on_dist));
    g_cp_color = g_sec.create_colorpicker("Marker Color", g_color);
    g_cp_color.on_change(cast<int64>(on_color));
    g_sec.create_separator();
    button_t save_btn = g_sec.create_button("Save Config", ui_align::right);
    save_btn.on_change(cast<int64>(on_save));
}
