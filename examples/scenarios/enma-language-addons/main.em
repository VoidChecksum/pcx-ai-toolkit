import "json";

int64 main() {
    json_value payload = json_parse("{\"name\":\"pcx\",\"count\":2}");
    string encoded = json_stringify(payload);
    println(encoded);

    int64[] values = {1, 2};
    values.push(3);

    map<string, int64> counts;
    counts.set("examples", values.length());
    return counts.get("examples");
}
