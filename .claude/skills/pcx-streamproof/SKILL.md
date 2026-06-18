# Streamproof Overlay — Capture Compatibility for PCX Renders

When PCX overlay output shows up in screen captures and when it doesn't, mapped per capture method (OBS, Discord, GeForce ShadowPlay, NVIDIA Highlights, PrintScreen, Steam screenshot, capture cards). The user-recurring questions "why does my friend on Discord see my menu" and "I want my overlay invisible on stream" both reduce to which capture path each viewer is using and which PCX render surface they're seeing — this skill makes that mapping explicit.

**Trigger when:** the user mentions OBS, Twitch, streaming, capture card, Discord screenshare, GeForce Experience, ShadowPlay, NVIDIA Highlights, Steam screenshot, PrintScreen, NVENC, Elgato, replay buffer, instant replay, "my overlay shows on stream," "my friend can see my menu," or related capture / recording questions.

**Prerequisite:** `docs/perception/render-api.md` for the actual render surface taxonomy on your PCX build; `knowledge/anti-cheat-architecture.md` for context on screenshot-based scans by anti-cheats.

---

## Trigger

Streaming, recording, screen-share, capture-card, screenshot, replay-buffer, NVIDIA/AMD overlay coexistence questions; reports of friends seeing things on Discord, viewers seeing menus on Twitch, an overlay artifact appearing in a saved screenshot.

---

## 1. Capture Taxonomy — How Each Capture Method Sees the Screen

**The single fact that explains every "why can my friend see this" question: different capture methods see different layers of the rendering stack. They are not interchangeable.**

| Capture Method | What It Captures | Common Software |
|---|---|---|
| **Game Capture / Window Capture (hook)** | Hooks the game process's D3D/Vulkan/OGL swap chain; captures the frame *before* it composites with other overlays | OBS "Game Capture", Streamlabs, Twitch Studio |
| **Display Capture (DXGI Desktop Duplication)** | Captures the final composited desktop image as DWM composes it | OBS "Display Capture", Discord screenshare, Windows screenshot, Snipping Tool |
| **GPU-driver capture** | Driver-level hook of the game's render output, before window composition | NVIDIA ShadowPlay, NVIDIA Highlights, AMD ReLive |
| **Print-window GDI** | Bitblts a specific window's GDI surface | Legacy screen-capture tools, `PrintScreen` on some configurations |
| **Capture card (HDMI)** | Captures the GPU output signal at the cable; sees exactly what the monitor sees | Elgato, AverMedia, dedicated streaming PC setups |
| **Mirror driver** | Inserts a virtual display device that mirrors what would have rendered | Some VPN/remote-access tools, older streaming setups |

Three categories matter:

1. **Process-internal capture** (Game Capture, ShadowPlay) — sees only what the game process renders into its own swap chain
2. **Desktop-composited capture** (Display Capture, Discord screenshare, screenshot tools) — sees the final image after DWM merges everything
3. **Signal-level capture** (HDMI capture card) — sees the final pixels on the wire to the monitor

A PCX overlay can be visible to any subset of these depending on how it's rendered. The default question to ask any user with a capture problem is: "which of these three categories is the viewer using?"

**Why:** Most "but my friend can see it" reports are actually "my friend uses Discord screenshare (desktop-composited), and you tested with OBS Game Capture (process-internal) — different layers, different results." Pin the capture method before debugging anything else.

---

## 2. PCX Render Surface Behavior

**PCX provides multiple ways to put pixels on screen. Each one lands in a different layer of the rendering stack, and that determines which capture methods see it. The exact surface names and modes are in `docs/perception/render-api.md` — read it for your PCX version.**

The general mapping (verify against your build's docs):

| PCX Render Path | Lands In | Visible to Game Capture? | Visible to Display Capture? | Visible to ShadowPlay? | Visible to HDMI Capture? |
|---|---|---|---|---|---|
| **Direct game-process render** (overlay drawn into the game's own swap chain via PCX's swap-chain hook) | The game's swap chain, before window composition | Yes | Yes (via the composited desktop) | Yes | Yes |
| **External overlay window** (PCX renders to a separate top-most layered window) | A separate window, composited by DWM into the desktop | No (Game Capture only sees the game window) | Yes | No (driver capture is per-game) | Yes |
| **DWM composition layer hook** (where supported) | Inserted into the DWM composition pipeline | Varies by platform; treat as Display Capture in practice | Yes | No | Yes |
| **GPU compute shader visualization** (custom shader output) | Depends on how PCX exposes the shader output — typically composited similar to one of the above | Same as the surface it composites into | Same | Same | Same |

The pattern: anything that ends up *inside the game process's render output* is visible to everything. Anything that's a *separate window or DWM layer* is invisible to in-game-process captures (Game Capture, ShadowPlay) but visible to anything that captures the composited desktop.

**Why:** Capture-card and desktop-capture methods see "what the user sees" — so anything visible to the user is visible to them, period. The only capture paths that distinguish overlays from the game's own rendering are the process-internal ones, and they distinguish based on which process's swap chain the overlay landed in.

---

## 3. The Pre-Stream Checklist

**Before going live, validate against the capture method you actually use. A test against OBS Game Capture tells you nothing about what shows up on Discord screenshare.**

```
For each capture method the user cares about (typically Twitch + Discord):

[ ] Open the capture in preview (OBS preview pane, Discord call with self-view, etc.)
[ ] Walk through every PCX render path you have enabled:
    - Main overlay
    - Menu / GUI sections
    - Notification popups
    - Any custom shader output
[ ] For each: is it visible in the preview?
[ ] If visible-but-wanted-hidden: switch to a render path that doesn't land in this capture's layer
[ ] If wanted-visible-but-hidden: switch to one that does land in this capture's layer
[ ] Confirm by recording a 10-second clip and rewatching; previews are sometimes lossy
```

The matrix to fill before going live:

| Capture target | What I want visible | What I want hidden | Render path to use |
|---|---|---|---|
| Twitch stream (OBS Game Capture) | Game | PCX overlay | External overlay window |
| Twitch stream (OBS Display Capture) | Game + overlay | Nothing | Either render path; both visible |
| Discord screenshare | Same as Display Capture | Hard to hide; see Step 4 | External window won't help here |
| ShadowPlay highlight clip | Game | PCX overlay | External overlay window |
| Steam screenshot | Game | PCX overlay | External overlay window |
| HDMI capture card | Both | Nothing hideable | All renders land here |

**Why:** Going live without checking is how the "my menu just showed up on stream during a clutch" story happens. Five minutes of preview-and-record is cheaper than a clip going around.

---

## 4. Capture Cards and HDMI Are Pixel-Accurate — No Software Solution

**An HDMI capture card sees the monitor signal. If the user sees it, the capture card sees it. There is no software-rendered overlay that avoids being captured by a downstream signal-level capture.**

The only options when a capture card is in play:

- **Dual-monitor setup with the overlay on the non-captured display** (e.g. menus on monitor 2 which is not piped to the capture card). Requires PCX to render to a specific display, which depends on the render-surface options in your build.
- **Use the in-game render path and accept it's visible** — then make the overlay aesthetically discreet (low alpha, small footprint, off-screen during gameplay) so it's not eye-catching even when visible.
- **Use a streaming PC topology** where the gaming PC's HDMI goes to a capture card on a *second* PC, and the second PC composites the streamer's webcam/scenes; the overlay still shows on the captured feed but you have more control over what's composited around it.

There is no clever DWM trick that defeats the HDMI signal — pixels are pixels by the time they reach the cable.

**Why:** Newcomers ask "how do I make my overlay invisible to my capture card" expecting a software answer. There isn't one; pin this fact early and shift the conversation to the topology / aesthetic options that actually work.

---

## 5. Screenshot-Based Detection by Anti-Cheats

**Some anti-cheats capture screenshots of the game window or full desktop and analyze them for known overlay artifacts. This is a separate concern from "streamproof for viewers" but uses the same capture-path taxonomy.**

The standard mechanisms (see `knowledge/anti-cheat-architecture.md` for per-AC details):

- **In-process screenshot** — AC code running inside the game process grabs the game's swap-chain backbuffer. Sees anything that landed in the game's render output. External overlay windows do not appear in this capture.
- **Desktop screenshot** — AC service captures the full desktop via DXGI. Sees everything the user sees. External overlay windows DO appear here.
- **Game-window PrintWindow** — AC calls `PrintWindow(hwnd, ...)` on the game window. Sees only what's GDI-rendered into that window (often misses D3D-composited overlays entirely).

Historical examples (from publicly documented behavior of the named systems — see `knowledge/anti-cheat-architecture.md`):

- BattlEye's `BEClient.dll` has been observed taking screenshots via in-process capture and uploading them for analysis.
- EAC includes screenshot capability invoked by backend rule pushes.
- Vanguard does in-process capture as part of its memory-integrity scanning.

The general principle: a render path that's invisible to a given capture *for viewers* is also invisible to a screenshot taken via the same mechanism. An overlay invisible to OBS Game Capture is also invisible to in-process AC screenshots. This is coincidental alignment with anti-evasion goals — the underlying mechanism is the same render-pipeline layering.

**Note:** the appropriate response to AC screenshot detection is platform terms-of-service compliance and `skill://anti-cheat-re` for understanding the detection surface. This skill maps the *what's visible to what* fact; it does not advise on evasion of legitimate platform enforcement.

**Why:** Users conflate "streamproof" with "AC-invisible" — they aren't the same goal, but they share a technical foundation (which render surface is in which capture layer). Splitting the goals clarifies which question you're answering and prevents over-claiming "this is invisible to AC" when you've only verified one capture path.

---

## 6. Differential Diagnosis: "Friend on Discord Can See My Menu"

**The most-reported confusion. The user tests their overlay against OBS Game Capture (sees nothing — good), then a friend on Discord screenshare sees the menu. This is not a bug; it's the capture-path mismatch from Step 1.**

Standard diagnosis sequence:

1. Ask: how is the friend viewing? Discord screenshare, Discord camera passthrough, watching a Twitch stream, looking at a screenshot, watching a recorded clip?
2. Map their viewing method to a capture category from Step 1 (Discord screenshare → Display Capture; Twitch via OBS Game Capture → process-internal; etc.).
3. Confirm: the PCX render path the user is using lands in *that* capture's layer. (Refer to the Step 2 matrix.)
4. Options:
   - Switch the offending render path to one that doesn't land in the friend's capture layer
   - If unavoidable (Display Capture catches all visible overlays): change the workflow (different capture target, hide-toggle hotkey, render only off-screen)
   - If the friend uses a HDMI capture card: see Step 4 — no software fix

```
Concrete walkthrough:

User: "My friend on Discord can see my ESP."
You:  "Discord screenshare uses Display Capture (composited desktop). Your
       PCX overlay landing in either the game's swap chain OR a separate
       desktop window will both show up there.
       To hide it from Discord screenshare specifically, you'd need to
       hide the rendering itself — there's no render path that's visible
       to you-the-user but invisible to Display Capture, because both you
       and Display Capture see the same composited desktop."

User: "But I tested with OBS and it didn't show up!"
You:  "OBS Game Capture only hooks the game's swap chain. If your overlay
       renders to a separate window, OBS Game Capture misses it — but
       Discord screenshare (Display Capture) doesn't. Different layers,
       different visibility."
```

The honest answer to many "how do I hide this from Discord" questions is "you can't, because Discord screenshare sees the same desktop you do." Steer toward workflow changes (bind a hide hotkey, share game audio only, share a specific application window that excludes the overlay).

**Why:** The technical answer (capture-path layering) once explained becomes obvious in retrospect. The hours of "but why" questions disappear when the user understands the three-category model from Step 1.

---

## Summary

| # | Topic | One-liner |
|---|---|---|
| 1 | Capture taxonomy | Process-internal vs desktop-composited vs signal-level — three layers, different visibility |
| 2 | PCX render paths | Game-swap-chain hook vs external window vs DWM layer — each lands in a different capture layer |
| 3 | Pre-stream checklist | Validate against the specific capture method, not "a screen capture" generically |
| 4 | HDMI capture cards | Pixel-accurate; no software solution; topology and aesthetics only |
| 5 | AC screenshot detection | Uses the same capture taxonomy; alignment with streamproofing is coincidental, not by design |
| 6 | Differential diagnosis | "Friend on Discord sees X" almost always = capture-path mismatch, not a script bug |

**Cross-references:** `docs/perception/render-api.md` (authoritative surface list for your PCX version), `knowledge/anti-cheat-architecture.md` (per-AC screenshot mechanisms), `skill://anti-cheat-re` (detection-surface methodology), `skill://pcx-perf-budget` (overlay render cost considerations for streamers running on a single-PC topology).
