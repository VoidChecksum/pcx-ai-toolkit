# PCX Script Examples

Fully annotated, runnable example scripts demonstrating common PCX scripting patterns.
All examples follow the [12 coding guidelines](../rules/CLAUDE.md) and pass `pcx lint`.

## Examples

| Script | Language | Demonstrates |
|--------|----------|--------------| 
| [esp-overlay/esp-overlay.em](esp-overlay/esp-overlay.em) | Enma | ESP boxes, text rendering, world-to-screen, entity iteration |
| [aimbot-basic/aimbot-basic.em](aimbot-basic/aimbot-basic.em) | Enma | FOV check, bone targeting, mouse movement, smoothing |
| [memory-scanner/memory-scanner.em](memory-scanner/memory-scanner.em) | Enma | Pattern scanning, offset caching, sig-based resilience |

## How to Use

1. Copy the example directory to your project
2. Edit the signature constants to match your target game
3. Adjust offsets and entity structure definitions for your game version
4. Load in Perception.cx and verify with live reads
5. Run `pcx lint <file.em>` to validate against the 12 guidelines

## Guidelines Checklist

All examples demonstrate:
- ✅ `uint64` for all addresses (never `int64` or `int`)
- ✅ `f` suffix on all `float32` literals
- ✅ Null-check every pointer before dereferencing
- ✅ Separate update routine from render routine (no memory reads in render)
- ✅ Pattern signatures, not hardcoded offsets
- ✅ One feature per file
- ✅ Colors and vecs constructed fresh each frame
- ✅ World-to-screen with `w > 0` guard
- ✅ GUI controls for all tunables

## See Also

- `templates/` — starter templates for new projects
- `knowledge/common-patterns.md` — reusable code patterns
- `rules/CLAUDE.md` — the full 12 guidelines
