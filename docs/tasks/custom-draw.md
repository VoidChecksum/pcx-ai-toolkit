# Custom Draw

## Goal

Submit custom geometry through documented custom draw handles without inventing OpenGL/D3D pipeline calls.

## Load

- `docs/perception/custom-draw-api.md`
- `docs/perception/render-api.md`

## Exact Enma imports

`import "color";` and `import "vec";` for basic render helpers; custom draw vertex arrays use `float32[]`.

## Exact symbols

`custom_draw`, `TOPO_TRIANGLE_LIST`, `draw_triangle`, `vec2`, `color`.

## Permissions

No special permission for rendering. Handles from create/load calls are encrypted `int64`; pass them back unchanged.

## Enma example

```enma
import "vec";
import "color";

void render(int64 data) {
    color amber = color(255, 180, 60, 255);
    draw_triangle(vec2(80.0, 40.0), vec2(40.0, 120.0), vec2(120.0, 120.0), amber, 1.0, true);
}

int64 main() {
    register_routine(cast<int64>(render), 0);
    return 1;
}
```

## Failure and sentinel checks

Custom draw resource creation returns handles. Treat `0` as failure for resources; do not do arithmetic on handles. For simple triangles, prefer `draw_triangle` over a fake `create_pipeline` abstraction.

## Perception MCP equivalent

Use MCP `script/validate` for custom draw source. Use Perception runtime/editor for long-lived render execution; MCP process tools do not replace render APIs.

## Validate

```bash
pcx check-answer docs/tasks/custom-draw.md
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
