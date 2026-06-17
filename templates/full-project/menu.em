// menu.em — GUI sidebar + config persistence.
// Every tunable is a widget; config saves/loads via the filesystem API.

import "color";
import "globals";

void save_config() {
    string cfg = "";
    cfg = cfg + "enabled="  + cast<string>(g_enabled) + "\n";
    cfg = cfg + "max_dist=" + cast<string>(g_max_distance) + "\n";
    write_file("config.txt", cfg);
}

void load_config() {
    if (!file_exists("config.txt")) return;
    string cfg = read_file("config.txt");
    for (string line : cfg.split("\n")) {
        array<string> kv = line.split("=");
        if (kv.length() < 2) continue;
        if (kv[0] == "enabled")  g_enabled = (kv[1] == "true" || kv[1] == "1");
        if (kv[0] == "max_dist") g_max_distance = kv[1].to_float();
    }
}

void setup_menu() {
    load_config();
    int64 sec = create_section("Project");
    section_checkbox(sec, "Enabled", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_distance, 0.0, 10000.0);
    section_color_picker(sec, "Marker Color", g_color);
    section_separator(sec);
    section_button(sec, "Save Config", cast<int64>(save_config));
}
