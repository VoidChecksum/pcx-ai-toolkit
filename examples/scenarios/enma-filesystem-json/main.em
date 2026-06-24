import "json";

int64 main() {
    string path = "pcx-scenario.json";
    json_value payload = json_parse("{\"ok\":true}");
    string encoded = json_stringify(payload);
    if (!fs_write_file(path, encoded)) {
        return 0;
    }
    string loaded = fs_read_file(path);
    return loaded.length();
}
