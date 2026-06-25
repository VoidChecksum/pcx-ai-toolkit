# HTTP Request

## Goal

Make a bounded HTTP request and handle status `0` as transport/permission failure.

## Load

- `docs/perception/net-api.md`

## Exact Enma imports

No extra import is required beyond the Net API registration in Perception scripts.

## Exact symbols

`http_get`, `http_post`, `http_response_t.status`, `http_response_t.ok`, `http_response_t.body`.

## Permissions

Requires host network/API permission when Perception gates outbound requests. Never assume exceptions or async/await.

## Enma example

```enma
// Requires network_access permission.
int64 main() {
    http_response_t r = http_get("https://api.example.com/status", 5000);
    if (r.status() == 0) {
        println("[net] transport failed or permission denied");
        return 0;
    }
    if (!r.ok()) {
        println("[net] status=" + cast<string>(r.status()));
        return 0;
    }

    println(r.body());
    return 1;
}
```

## Failure and sentinel checks

`status() == 0` means transport failure or permission denial. HTTP 4xx/5xx are real responses; handle them separately from `0`.

## Perception MCP equivalent

MCP is for controlling Perception and inspecting processes, not making arbitrary app HTTP requests. Use Enma Net API for runtime requests; use knowledge MCP docs/search for planning.

## Validate

```bash
pcx check-answer docs/tasks/net-http.md
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
