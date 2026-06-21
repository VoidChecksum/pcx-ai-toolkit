// menu.as — config, keybinds, save/load
namespace Cheat {

const string CONFIG_PATH = "cheat_skeleton_config.json";

void setup_menu() {
    load_config();

    create_checkbox("ESP",      g_esp_enabled);
    create_checkbox("Aimbot",   g_aim_enabled);
    create_slider("Aim Smooth", g_aim_smooth, 0.01, 1.0);
    create_slider("Aim FOV",    g_aim_fov,    1.0,  180.0);
    create_checkbox("Trigger",  g_trigger_enabled);
    create_checkbox("Radar",    g_radar_enabled);
    create_button("Save Config", save_config);
}

void save_config() {
    json_value root;
    root["esp_enabled"]     = json_bool(g_esp_enabled);
    root["aim_enabled"]     = json_bool(g_aim_enabled);
    root["aim_smooth"]      = json_float(g_aim_smooth);
    root["aim_fov"]         = json_float(g_aim_fov);
    root["trigger_enabled"] = json_bool(g_trigger_enabled);
    root["radar_enabled"]   = json_bool(g_radar_enabled);

    file_write(CONFIG_PATH, json_stringify(root, 2));
}

void load_config() {
    if (!file_exists(CONFIG_PATH)) return;
    string text = file_read(CONFIG_PATH);
    json_value root = json_parse(text);
    if (root.type() != JSON_OBJECT) return;

    g_esp_enabled     = root["esp_enabled"].as_bool(g_esp_enabled);
    g_aim_enabled     = root["aim_enabled"].as_bool(g_aim_enabled);
    g_aim_smooth      = root["aim_smooth"].as_float(g_aim_smooth);
    g_aim_fov         = root["aim_fov"].as_float(g_aim_fov);
    g_trigger_enabled = root["trigger_enabled"].as_bool(g_trigger_enabled);
    g_radar_enabled   = root["radar_enabled"].as_bool(g_radar_enabled);
}

}
