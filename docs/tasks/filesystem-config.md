# Filesystem Config

## Goal

Read and write a simple config file without treating empty strings as proof of missing files.

## Load

- `docs/perception/filesystem-api.md`
- `docs/tasks/gui-config.md`

## Exact Enma imports

`import "file";` and `import "strings";`

## API

`fs_file_exists`, `fs_read_file`, `fs_write_file`, `string.split`.

## Permissions

Requires `PERM_FILE` / `file_system_access`. Use relative paths; do not use absolute paths or `..` unless the host explicitly allows them.

## Minimal code

```enma
// Requires PERM_FILE / file_system_access.
import "file";
import "strings";

int32 g_value = 7;

void save_config() {
    fs_write_file("config.txt", "value=" + cast<string>(g_value) + "\n");
}

void load_config() {
    if (!fs_file_exists("config.txt")) {
        println("missing config; using defaults");
        return;
    }

    string body = fs_read_file("config.txt");
    for (string line : body.split("\n")) {
        string[] kv = line.split("=");
        if (kv.length() == 2 && kv[0] == "value") g_value = kv[1].to_int();
    }
}

int64 main() {
    load_config();
    println("value=" + cast<string>(g_value));
    save_config();
    return 1;
}
```

## Failure and sentinel checks

`fs_read_file` can return an empty string for missing/denied/read-error and for a valid empty file. Use `fs_file_exists` before reading when empty data is valid.

## Perception MCP equivalent

Use knowledge MCP `validate_code` or Perception MCP `script/validate` for generated config scripts. Runtime file I/O belongs in Enma, not process MCP.

## Validate

```bash
pcx check-answer docs/tasks/filesystem-config.md
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
