# Render Overlay

## Load

- `docs/AI_AGENT_OPERATING_MANUAL.md`
- `docs/perception/llm-routing.md`
- `docs/llms-perception-enma.md`

## API lookup symbols

draw_text, draw_line, draw_rect

## Permissions

render APIs

## Minimal code

```enma
import "vec";
import "color";
void render(int64 data){ draw_text("hi", vec2(20.0,20.0), color(255,255,255,255), get_font20(), 0, color(0,0,0,0), 0.0); }
int64 main(){ register_routine(cast<int64>(render),0); return 1; }
```

## Validate

```bash
pcx check-answer docs/tasks/render-overlay.md
pcx verify <file.em>
```

## Common hallucinations

- ImGui-style helpers
- generic C++/Lua/JavaScript helpers
- undocumented game-specific wrappers
- unchecked permission or sentinel failures

## Source links

- `docs/perception/llm-routing.md`
- `knowledge/pcx-api-index.json`
- `docs/COVERAGE.md`
