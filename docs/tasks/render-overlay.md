# Render Overlay

## Goal

Draw a long-lived overlay routine using documented Render APIs and Perception lifecycle semantics.

## Load

- `docs/perception/lifecycle-and-routines.md`
- `docs/perception/render-api.md`

## Exact Enma imports

`import "vec";` and `import "color";`

## API

`register_routine`, `draw_text`, `draw_rect`, `draw_line`, `vec2`, `color`, `get_font20`.

## Permissions

No special permission for basic render calls. Render work belongs in a registered routine, not a fake `on_render` callback.

## Minimal code

```enma
import "vec";
import "color";

void render(int64 data) {
    color white = color(255, 255, 255, 255);
    color green = color(80, 255, 120, 255);
    color none = color(0, 0, 0, 0);

    draw_rect(vec2(20.0, 20.0), vec2(220.0, 80.0), green, 1.0, 6.0, 15);
    draw_line(vec2(20.0, 100.0), vec2(240.0, 100.0), green, 1.0);
    draw_text("PCX overlay", vec2(32.0, 42.0), white, get_font20(), 1, none, 1.0);
}

int64 main() {
    register_routine(cast<int64>(render), 0);
    return 1;
}
```

## Failure and sentinel checks

Render calls return handles/sentinels that are normally not inspected for simple overlay primitives. Validate argument shape instead: `vec2` for positions/sizes, `color` for colors, exact argument counts.

## Perception MCP equivalent

Use MCP `script/validate` to compile-check generated overlay code. Use the in-app script editor for long-lived overlay execution; `script/execute` is one-shot and excludes GUI/thread addons.

## Validate

```bash
pcx check-answer docs/tasks/render-overlay.md
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
