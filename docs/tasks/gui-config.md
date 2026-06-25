# GUI Config

## Goal

Build a sidebar GUI, bind widget callbacks, and keep runtime state separate from saved config.

## Load

- `docs/perception/gui-api.md`
- `docs/perception/filesystem-api.md`
- `templates/full-project/menu.em`

## Exact Enma imports

`import "color";`, `import "file";`, and `import "strings";` when parsing text config.

## Exact symbols

`create_sidebar_section`, `checkbox_t`, `slider_t`, `colorpicker_t`, `fs_file_exists`, `fs_read_file`, `fs_write_file`.

## Permissions

GUI calls need no special permission. Config persistence requires `PERM_FILE` / `file_system_access`.

## Enma example

```enma
// Requires PERM_FILE / file_system_access for save/load.
import "color";
import "file";
import "strings";

bool g_enabled = true;
float64 g_range = 120.0;
checkbox_t g_cb;
slider_t g_slider;

void on_enabled(int64 h) { g_enabled = g_cb.get(); }
void on_range(int64 h) { g_range = g_slider.get(); }

void save_config() {
    string cfg = "enabled=" + cast<string>(g_enabled) + "\n";
    cfg = cfg + "range=" + cast<string>(g_range) + "\n";
    fs_write_file("config.txt", cfg);
}

void load_config() {
    if (!fs_file_exists("config.txt")) return;
    string cfg = fs_read_file("config.txt");
    for (string line : cfg.split("\n")) {
        string[] kv = line.split("=");
        if (kv.length() < 2) continue;
        if (kv[0] == "enabled") g_enabled = (kv[1] == "true" || kv[1] == "1");
        if (kv[0] == "range") g_range = kv[1].to_float();
    }
}

int64 main() {
    load_config();
    sidebar_section_t sec = create_sidebar_section("PCX", "");
    g_cb = sec.create_checkbox("Enabled", g_enabled);
    g_cb.on_change(cast<int64>(on_enabled));
    g_slider = sec.create_slider("Range", g_range, 0.0, 500.0, 1.0);
    g_slider.on_change(cast<int64>(on_range));
    return 1;
}
```

## Failure and sentinel checks

Check file existence before `fs_read_file` so empty config is not confused with missing file. Save only on explicit user action or controlled callback.

## Perception MCP equivalent

Use MCP `script/validate` to compile-check GUI code. Do not use `script/execute` for GUI; it intentionally excludes GUI addons to avoid one-shot leaks.

## Validate

```bash
pcx check-answer docs/tasks/gui-config.md
pcx verify <file.em>
```

## When to use Perception MCP instead of Enma

Use Enma for long-lived scripts, overlays, GUI, per-frame reads, and logic that runs inside Perception. Use Perception MCP for one-shot inspection, string/xref discovery, function bounds, signature generation, script validation from an agent, and stale-handle/error recovery.

## Common hallucinations

- Inventing helper APIs instead of checking `pcx api <symbol>`.
- Passing raw `x, y` or RGBA integers instead of `vec2(...)` and `color(...)`.
- Treating sentinel `0`, `false`, empty arrays, or empty strings as exceptions.
- Skipping permission notes for process, file, net, write, or kernel-gated work.

## Related skills

- `.claude/skills/mcp-tool-routing/SKILL.md`
- `.claude/skills/pcx-re-discipline/SKILL.md`
- `docs/AI_AGENT_OPERATING_MANUAL.md`

## Source links

- `docs/perception/mcp-api.md`
- `docs/perception/two-mcp-workflow.md`
- `knowledge/pcx-api-index.json`
