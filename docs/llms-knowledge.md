# pcx-ai-toolkit — Knowledge Bundle

> Every knowledge reference in the pcx-ai-toolkit concatenated into one file. Covers engine RE references, anti-cheat architecture, common scripting patterns, aimbot math, API cheatsheets, GUI design, multi-binary organization, network protocol RE, and the cross-language bridge.

> **Generated** by `tools/build-llms-index.py` — do not edit manually. Re-generate by running the tool from the repo root. CI verifies the committed bundle matches the current source.

**Source files included: 26**

---

## Source: `knowledge/aimbot-math.md`

# Aimbot Math Reference

> **Scope:** Educational math reference for PCX cheat development. Authorized targets only.

This is the math companion to [`common-patterns.md`](common-patterns.md). That file
covers the *render* half — world-to-screen, boxes, snaplines, radar — plus a single
`calc_angle` / `smooth_angle` teaser. The README promises "angle calc, smooth interp"
for the aim half; this file is where that math actually lives. Everything below builds
on the Enma idioms already established in `common-patterns.md`: `uint64` addresses,
`proc_t` reads, `vec3` field access (`.x` / `.y` / `.z`, no getter parens), and the
`(180.0 / PI)` degree conversion used by `calc_angle`.

Code blocks honor the 12 [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md):
`uint64` addresses, caller null-guards every read, scan stays out of render, and the one
feature that writes memory (no-recoil, angle writeback) writes the minimum bytes. Offsets
appear as bare symbolic identifiers (`OFF_VELOCITY`, resolved in `offsets.em`) exactly as
`common-patterns.md` does — never a version-specific hex literal.

```cpp
// Shared throughout this reference. Matches common-patterns.md calc_angle.
const float64 PI = 3.14159265358979;
const float64 RAD2DEG = 180.0 / PI;
const float64 DEG2RAD = PI / 180.0;
```

## Angles: yaw and pitch from two world points

The aimbot's core question — "what view angles point my camera at that target?" — answers with
two `atan2` calls. This is `calc_angle` from `common-patterns.md`, restated with the convention
spelled out:

```cpp
// Returns (pitch, yaw) in degrees. Source-engine convention (z = up).
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta = dst.sub(src);                          // dst - src
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * RAD2DEG; // up = negative pitch
    float64 yaw   = atan2(delta.y, delta.x) * RAD2DEG;
    return vec2(pitch, yaw);                             // vec2.x = pitch, vec2.y = yaw
}
```

**Output range.** `atan2` returns `(-PI, PI]`, so pitch and yaw come out in `(-180, 180]` — the
range Source-family games store. If your engine stores yaw in `[0, 360)`, normalize *on
writeback*, not here; the delta math below wraps either input correctly.

**Pitch sign is engine-specific and trips everyone.** `atan2(-delta.z, dist_xy)` produces
a *negative* pitch when the target is above you (`delta.z > 0`). That matches Source, where
looking up is negative pitch. Other engines flip this:

| Engine          | Angle storage           | Up is...        | Yaw zero axis | Handedness |
| --------------- | ----------------------- | --------------- | ------------- | ---------- |
| Source / Source2| `QAngle{pitch,yaw,roll}`, degrees | negative pitch | +X | left, z-up |
| Unreal (UE4/5)  | `FRotator{Pitch,Yaw,Roll}`, degrees | positive pitch | +X | left, z-up |
| Unity           | Euler degrees / quaternion | positive pitch | +Z | left, y-up |

For Unreal, drop the negation: `pitch = atan2(delta.z, dist_xy) * RAD2DEG`. For Unity the "up"
axis is `y`, so `dist_xy` is the XZ-plane distance and pitch keys off `delta.y`.

## Angle deltas — the wrap-around trap

You never write absolute angles into a smoothing loop; you work with the *delta* from your
current view to the target. Subtracting two angles naively breaks at the seam where the
range wraps.

Suppose your current yaw is `350°` and the target is at `10°`. The shortest turn is `+20°`
(swing right through `360°/0°`). But `target - current = 10 - 350 = -340°` tells the
aimbot to spin almost all the way around the other direction. Symmetrically, current `10°`
to target `350°` should be `-20°`, not `+340°`.

The fix maps any delta into `[-180, 180)`:

```cpp
// Normalize an angle delta (degrees) to the shortest signed path in [-180, 180).
float64 normalize_delta(float64 delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}
```

**Why `+540`, not `+180`?** `540 = 360 + 180`. Enma's `fmod` follows C semantics: the
result takes the sign of the dividend, so `fmod(-340.0, 360.0)` is a *negative* `-340`, not
`20`. Offsetting by `540` guarantees the argument is positive for any delta in `[-360, 360]`
(`delta + 540` lands in `[180, 900]`), so `fmod` stays positive, and the trailing `- 180`
re-centers it. Verify:

```
normalize_delta(-340) = fmod(200, 360) - 180 = 200 - 180 = +20   // 350 -> 10, correct
normalize_delta(+340) = fmod(880, 360) - 180 = 160 - 180 = -20   // 10 -> 350, correct
normalize_delta(+10)  = fmod(550, 360) - 180 = 190 - 180 = +10   // no wrap, unchanged
```

Apply it to yaw on every frame. Pitch does **not** wrap (it is clamped to roughly
`[-89, 89]`), so clamp pitch instead of wrapping it:

```cpp
vec2 angle_delta(vec2 current, vec2 target) {
    float64 dp = fclamp(target.x - current.x, -89.0, 89.0);  // pitch: clamp, no wrap
    float64 dy = normalize_delta(target.y - current.y);      // yaw: wrap
    return vec2(dp, dy);
}
```

## FOV cone check — "is the target in screen FOV"

Two formulations. They answer slightly different questions; pick by what you already have.

**3D angle cone (dot product).** Use this when you have view angles and world positions and
have *not* run world-to-screen yet (cheaper — no matrix multiply). Build the view-forward
unit vector from your angles, build the unit direction to the target, and compare their dot
product against `cos(fov)`:

```cpp
// Forward unit vector from Source-convention view angles (degrees).
vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * DEG2RAD;
    float64 y = yaw_deg * DEG2RAD;
    float64 cp = cos(p);
    return vec3(cp * cos(y), cp * sin(y), -sin(p));  // -sin(p): up = negative pitch
}

// True if target sits within `fov_deg` half-angle of where the camera looks.
bool in_fov_cone(vec3 eye, vec2 view_angles, vec3 target, float64 fov_deg) {
    vec3 fwd = angles_to_forward(view_angles.x, view_angles.y);  // already unit length
    vec3 dir = target.sub(eye).normalize();
    float64 cos_limit = cos(fov_deg * DEG2RAD);
    return fwd.dot(dir) >= cos_limit;   // larger dot = smaller angle = inside cone
}
```

The dot of two unit vectors is `cos(angle_between)`. A wider FOV means a *smaller*
`cos_limit`, so the `>=` test loosens as `fov_deg` grows — exactly what you want.

**2D screen-space (pixel radius).** Use this when you already projected the target with
`world_to_screen` (from `common-patterns.md`). FOV becomes a pixel circle around the
crosshair (screen center):

```cpp
// True if the projected target is within `radius_px` of the crosshair.
bool in_fov_screen(vec2 target_screen, float64 radius_px) {
    float64 cx = get_view_width()  * 0.5;
    float64 cy = get_view_height() * 0.5;
    float64 dx = target_screen.x - cx;
    float64 dy = target_screen.y - cy;
    return (dx * dx + dy * dy) <= (radius_px * radius_px);  // squared: no sqrt needed
}
```

**Which to use.** The screen form is intuitive (a circle the user tunes in pixels) and honors
the game's real FOV/zoom for free since the projection already did. The 3D cone needs no
projection and works for off-screen targets, so it is the better gate for a closest-target
search over the full entity list. Many aimbots use the cone to *select* and the circle to
*display* the FOV ring.

## Closest target selection

Once the FOV gate passes, rank the survivors and pick one. Four metrics, increasing cost
and increasing "feel":

**By screen distance (2D).** Pixels from crosshair. Cheapest after projection; matches what
the player sees. This is what most "FOV aimbots" use:

```cpp
float64 score_screen(vec2 target_screen) {
    float64 dx = target_screen.x - get_view_width()  * 0.5;
    float64 dy = target_screen.y - get_view_height() * 0.5;
    return dx * dx + dy * dy;   // squared px; smaller = closer to crosshair
}
```

**By angular distance (3D).** The turn the aimbot must make, in degrees. Independent of FOV
zoom and screen resolution. Reuse `angle_delta`:

```cpp
float64 score_angular(vec2 view_angles, vec2 target_angles) {
    vec2 d = angle_delta(view_angles, target_angles);
    return sqrt(d.x * d.x + d.y * d.y);   // degrees of correction needed
}
```

**By world distance.** Closest in meters (`distance_3d` from `common-patterns.md`). Useful for
melee/shotgun logic, but a distant target dead-center beats a close one at the screen edge, so
world distance alone aims poorly.

**Hybrid weighted.** Prefer targets both near the crosshair *and* close. Normalize each term to
`[0, 1]` against its max, then weight:

```cpp
// Lower score wins. ang_w + dist_w should sum to 1.0.
float64 score_hybrid(float64 ang_deg, float64 max_ang,
                     float64 world_dist, float64 max_dist,
                     float64 ang_w, float64 dist_w) {
    float64 ang_n  = fclamp(ang_deg    / max_ang,  0.0, 1.0);
    float64 dist_n = fclamp(world_dist / max_dist, 0.0, 1.0);
    return ang_w * ang_n + dist_w * dist_n;
}
```

Worked example (`ang_w=0.7`, `dist_w=0.3`, `max_ang=30°`, `max_dist=3000`): target A (`5°` at
`2500`) → `0.7*(5/30)+0.3*(2500/3000)=0.367`; target B (`15°` at `400`) → `0.390`. A wins, the
smaller turn dominates. Bias toward angle for twitchy aim, toward distance to lock the nearest.

Selection loop picks the minimum score over the validated, in-FOV set:

```cpp
int32 best = -1;
float64 best_score = 1.0e30;
for (int32 i = 0; i < g_candidates.length(); i++) {
    float64 s = score_hybrid(g_ang[i], 30.0, g_dist[i], 3000.0, 0.7, 0.3);
    if (s < best_score) { best_score = s; best = i; }
}
```

## Target validation gate

Selecting a target is worthless if it is dead, friendly, or behind a wall. Run an **ordered**
checklist — cheap field reads first, the expensive line-of-sight trace last — and bail at the
first failure so you never trace a target you already rejected. (Separate scan from render:
this runs in `on_update`, not `on_render`.)

```cpp
bool is_valid_target(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos,
                     int32 local_team, float64 max_dist) {
    // 1. Alive (one int read — cheapest).
    if (p.r32(ent + OFF_HEALTH) <= 0) return false;

    // 2. Enemy team (one int read).
    if (p.r32(ent + OFF_TEAM) == local_team) return false;

    // 3. In range (no read; pure math on cached positions).
    if (target_pos.distance(eye) > max_dist) return false;

    // 4. Not smoked / flag-gated (one read; engine-specific flags).
    if ((p.ru32(ent + OFF_FLAGS) & FLAG_BLOCKED) != 0) return false;

    // 5. Visible — line of sight. The expensive check goes LAST.
    //    Prefer the engine's per-bone visible flag when it exists (one read);
    //    fall back to a ray trace only when it doesn't.
    if (p.r32(ent + OFF_VISIBLE) == 0) return false;

    return true;
}
```

**Ordering rationale.** Checks 1-4 are single integer reads or cached-position math —
nanoseconds. A visibility *trace* (casting a ray through the game's collision world, or
calling its `TraceLine`) is orders of magnitude more expensive and may require a write to set
up trace parameters. Gate it behind everything cheaper. If the engine exposes a
`m_bSpotted` / visible-bone bitmask (a plain read), prefer that over a trace entirely — it is
both cheaper and quieter. Offsets shown (`OFF_HEALTH`, `OFF_TEAM`, `OFF_FLAGS`, `OFF_VISIBLE`)
resolve in `offsets.em`; mark any you guessed `// UNVERIFIED` per guideline 12.

## Prediction — basic linear

Bullets are not hitscan in most games; they take time to arrive, and the target keeps moving.
Linear prediction extrapolates the target along its velocity by the bullet's travel time:

```
predicted = target_pos + target_vel * t,   where t = distance / bullet_speed
```

The catch: `distance` depends on where you aim, which depends on `t`, which depends on
`distance`. Solve it with a couple of fixed-point iterations — each pass refines `t` using
the previous pass's aim point. Two or three iterations converge for any reasonable speed:

```cpp
vec3 predict_linear(proc_t& p, uint64 ent, vec3 eye, vec3 target_pos, float64 bullet_speed) {
    vec3 vel = p.read_vec3_fl32(ent + OFF_VELOCITY);   // units/sec; read once
    vec3 aim = target_pos;
    for (int32 i = 0; i < 3; i++) {
        float64 t = aim.distance(eye) / bullet_speed;  // bullet flight time
        aim = target_pos.add(vel.scale(t));            // target_pos + vel*t
    }
    return aim;
}
```

**Getting bullet speed is game-dependent.** It is not a universal constant — it is per-weapon
muzzle velocity, often stored on the active weapon entity or a weapon-data table:

- **Source / Source2:** weapon script `CSWeaponData` / `WeaponInfo` exposes a projectile or
  muzzle speed; some weapons are hitscan (treat `t = 0`). Read the active weapon, then its
  data pointer.
- **Unreal:** the projectile class's `InitialSpeed` on `ProjectileMovementComponent`.
- **Generic:** if you cannot find a field, measure it — fire once at a wall a known distance
  away and time the impact, then hardcode per-weapon (and re-measure after patches).

Velocity itself comes from the target's movement field (`OFF_VELOCITY`, frequently
`m_vecVelocity`). If the game only stores positions, derive velocity as
`(pos_this_frame - pos_last_frame) / frametime` in `on_update`.

## Prediction — gravity-aware

When the projectile arcs (grenades, arrows, tank shells, Apex sniper drop), linear prediction
under-aims: you must both *lead* the moving target and *raise* the aim to fight gravity.

**Step 1 — intercept time against a moving target.** Treat the projectile as traveling at
constant speed `s` (handle the arc as a separate vertical correction). Let `pRel =
target_pos - shooter_pos` and `vt = target_vel`. The projectile reaches the target when the
straight-line distance it has flown equals the moving target's distance:

```
|pRel + vt*t| = s*t
```

Square both sides and group by powers of `t`:

```
(vt·vt - s²) t² + 2(pRel·vt) t + (pRel·pRel) = 0
       a              b               c
```

A standard quadratic. Take the **smallest positive** root (earliest interception):

```cpp
// Returns intercept time t > 0, or -1.0 if no real solution (target outruns projectile).
float64 intercept_time(vec3 p_rel, vec3 vt, float64 s) {
    float64 a = vt.dot(vt) - s * s;
    float64 b = 2.0 * p_rel.dot(vt);
    float64 c = p_rel.dot(p_rel);

    if (fabs(a) < 0.0001) {                 // target speed == projectile speed: linear
        if (fabs(b) < 0.0001) return -1.0;
        float64 t = -c / b;
        return t > 0.0 ? t : -1.0;
    }

    float64 disc = b * b - 4.0 * a * c;
    if (disc < 0.0) return -1.0;            // unreachable
    float64 sq = sqrt(disc);
    float64 t1 = (-b - sq) / (2.0 * a);
    float64 t2 = (-b + sq) / (2.0 * a);

    // Smallest strictly-positive root.
    float64 best = -1.0;
    if (t1 > 0.0) best = t1;
    if (t2 > 0.0 && (best < 0.0 || t2 < best)) best = t2;
    return best;
}
```

**Step 2 — gravity drop.** With the intercept time known, the lead point is
`target_pos + vt*t`. Gravity pulls the projectile down by `0.5 * g * t²` over that flight, so
aim that much *higher* (z is up in Source). `g` is the game's projectile gravity (often the
world gravity scaled by a per-projectile multiplier — read it, don't assume `9.8`):

```cpp
// Full gravity-aware aim point. Returns target_pos if unreachable.
vec3 predict_gravity(vec3 shooter, vec3 target_pos, vec3 target_vel,
                     float64 proj_speed, float64 gravity) {
    vec3 p_rel = target_pos.sub(shooter);
    float64 t = intercept_time(p_rel, target_vel, proj_speed);
    if (t < 0.0) return target_pos;                 // no firing solution; caller skips shot

    vec3 lead = target_pos.add(target_vel.scale(t)); // lead the motion
    lead.z = lead.z + 0.5 * gravity * t * t;         // raise to fight the drop
    return lead;
}
```

Feed `lead` into `calc_angle(eye, lead)` to get the firing angles. The drop term assumes z-up;
for a y-up engine (Unity) adjust `lead.y` instead. If `intercept_time` returns `-1`, there is
no firing solution — the target is faster than the projectile or out of range — so withhold
the shot rather than aiming at a garbage point.

## Recoil compensation (no-recoil)

A recoil pattern is a per-shot kick table: each consecutive round adds a known offset to the
view angles (a "spray pattern"). The game tracks how many rounds you have fired and the
accumulated punch, then offsets your aim by it. No-recoil cancels that offset.

Two approaches, cheapest first:

**Read and subtract the punch (read-mostly).** Most engines expose the accumulated aim punch
as a vector (`m_aimPunchAngle` in Source) and a shot counter (`m_iShotsFired`). Read the punch
and subtract it from your view angles when you write them back. This is the quiet path — you
only ever write the view-angle field you were going to write anyway for aim:

```cpp
// Returns view angles with the current recoil punch removed.
// OFF_PUNCH / OFF_VIEW_ANGLES resolve in offsets.em; UNVERIFIED until checked against binary.
vec2 compensate_recoil(proc_t& p, uint64 local, vec2 desired_angles) {
    vec3 punch = p.read_vec3_fl32(local + OFF_PUNCH);  // (pitch, yaw, roll) punch in degrees
    // Source scales stored punch by 2.0 for the actual view offset; verify per engine.
    return vec2(desired_angles.x - punch.x * 2.0,
                desired_angles.y - punch.y * 2.0);
}
```

**Patch the punch source (write, heavier footprint).** Some scripts zero the recoil-spread
float in game memory so the gun never kicks. Per guideline 9, write the single float, never a
NOP sled over the recoil code:

```cpp
// WRONG — nop-patching the recoil routine (16 bytes in .text, integrity-checked).
// RIGHT — zero the spread float that the routine reads.
if (g_norecoil) p.wf32(local + OFF_RECOIL_SPREAD, 0.0f);
```

Prefer the read-and-subtract path: it leaves zero write footprint on the recoil system and
folds cleanly into the angle you already plan to write. Reading the shot index (`m_iShotsFired`)
lets you ramp compensation in only while a spray is active, so single taps stay untouched.

## Smoothing — why and how

Snapping the view instantly onto a target is the loudest aim-detection signal: human aim has a
measurable acceleration curve and overshoot, a teleport does not, and behavioral anti-cheats
flag the zero-frame angle jump directly. Smoothing spreads the correction over several frames.
Always smooth the *delta* (wrapped via `normalize_delta`), never raw absolute angles, or the
yaw seam will make the view spin.

**Linear (divide).** Move a fixed fraction of the remaining delta each frame. This is
`smooth_angle` from `common-patterns.md`. Simple, but the speed decays as you close in, giving
a soft ease-out:

```cpp
vec2 smooth_linear(vec2 view, vec2 target, float64 smooth_factor) {
    vec2 d = angle_delta(view, target);                 // wrapped pitch+yaw delta
    return vec2(view.x + d.x / smooth_factor,           // larger factor = slower
                view.y + d.y / smooth_factor);
}
```

**Exponential (frame-rate independent).** The divide form above is tied to frame rate —
faster FPS means more steps means snappier aim. Decouple it from frame rate by deriving the
blend factor from elapsed time:

```cpp
vec2 smooth_exp(vec2 view, vec2 target, float64 rate, float64 dt) {
    float64 a = 1.0 - exp(-rate * dt);   // dt = 1.0 / get_fps(); a in (0,1)
    vec2 d = angle_delta(view, target);
    return vec2(view.x + d.x * a, view.y + d.y * a);
}
```

**Spring-damped (SmoothDamp).** Tracks angular velocity so the view *accelerates* into the turn
and eases out without overshoot — the most human-looking profile. `smooth_time` is the
approximate seconds to converge. It returns the new angle *and* the new velocity packed in a
`vec2`; persist `.y` per axis and feed it back next frame:

```cpp
// Critically-damped smoothing for one axis. Returns vec2(new_angle, new_velocity).
vec2 smooth_damp(float64 cur, float64 target, float64 vel, float64 smooth_time, float64 dt) {
    float64 omega = 2.0 / smooth_time;
    float64 x = omega * dt;
    float64 decay = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x);
    float64 change = cur - target;
    float64 temp = (vel + omega * change) * dt;
    float64 new_vel = (vel - omega * temp) * decay;
    return vec2(target + (change + temp) * decay, new_vel);
}
```

| Method        | Feel               | State | Frame-rate safe | Cost |
| ------------- | ------------------ | ----- | --------------- | ---- |
| Linear divide | ease-out only      | none  | no              | tiny |
| Exponential   | ease-out, smooth   | none  | yes (uses `dt`) | tiny |
| Spring-damped | ease-in + ease-out | per-axis velocity | yes | small |

**Sample-rate considerations.** Any tuning constant that is not time-based drifts with frame
rate — feed `dt = 1.0 / get_fps()` into the exponential and spring forms. The linear divide
form has no `dt`, so its effective speed differs between 60 and 240 FPS; document the slider as
frame-rate dependent or convert it to the exponential form.

## Mouse input writeback paths

Computed angles have to *become* aim somehow. Two routes, with very different detection
surfaces.

**Synthetic mouse input (`SendInput`).** Convert the angle delta to mouse counts and feed it
through the OS input stack via the Win API. The game sees ordinary mouse movement and applies
its own sensitivity, so the conversion needs the game's yaw/pitch-per-count factor:

```cpp
// Convert a view-angle delta (degrees) to relative mouse counts and send it.
// `counts_per_deg` is game sensitivity dependent — derive or measure it; UNVERIFIED.
void writeback_sendinput(vec2 angle_delta_deg, float64 counts_per_deg) {
    int64 dx = cast<int64>(angle_delta_deg.y * counts_per_deg);   // yaw  -> horizontal
    int64 dy = cast<int64>(angle_delta_deg.x * counts_per_deg);   // pitch -> vertical
    mouse_move_relative(dx, dy);   // or send_mouse_input(dx, dy, MOUSEEVENTF_MOVE, 0)
}
```

- *Pros:* no game-memory write at all — the cleanest footprint against memory-integrity
  checks; the movement rides the input path the game already trusts.
- *Cons:* synthetic input is itself detectable (injected-input flags, delta-timing analysis)
  and needs the sensitivity conversion, which shifts with the player's sens and zoom.

**Direct view-angle write.** Write the computed angles straight into the game's view-angle
field:

```cpp
void writeback_angles(proc_t& p, uint64 local, vec2 angles) {
    // OFF_VIEW_ANGLES resolves in offsets.em. One vec write per active frame, no more.
    p.write_vec3_fl32(local + OFF_VIEW_ANGLES, vec3(angles.x, angles.y, 0.0));
}
```

- *Pros:* exact — no sensitivity math, the view lands precisely where you computed.
- *Cons:* it is a memory write to a contested gameplay field; anti-cheat can monitor the
  field for writes that did not originate from the input path, and on a contested field the
  game may revert it (read back to confirm, per guideline 9).

**Respect guideline 9 either way.** Whichever path, write only while the aim key is held and
only the minimum needed — one relative move or one `write_vec3_fl32` per active frame, gated
on a GUI keybind. Never write every frame unconditionally:

```cpp
void on_update(int64 data) {
    if (!g_aim_enabled) return;
    if (!key_down(vk::xbutton2)) return;   // hold-to-aim; no key, no write
    // ... select + validate + predict + smooth, then a single writeback ...
}
```

## Common pitfalls

**Radians vs degrees — the silent 57× bug.** `atan2` and all Enma trig work in radians; most
view-angle fields store degrees, some store radians. The classic failure: read a radian-stored
angle, treat it as degrees, then write your degree result back into a radian field — everything
is off by `180/PI ≈ 57.3×` and the aim flicks to nonsense. Convert at *every* boundary
(`* RAD2DEG` after a trig call, `* DEG2RAD` before one) and confirm the field's unit by reading
it while looking at a known angle in-game.

**Pitch sign convention.** Source uses up = *negative* pitch; Unreal and Unity use up =
*positive* pitch. Backwards, and the aimbot pulls *down* onto targets above you and the spray
compensation fights the recoil instead of canceling it. Verify by reading the field while
aiming straight up.

**Left- vs right-handed coordinates.** Source/Unreal are left-handed z-up; Unity left-handed
y-up; many math libraries and custom W2S assume right-handed. A mismatch flips a yaw or
cross-product sign, so left-side targets read as right-side. If lead prediction consistently
aims to the wrong side, suspect a flipped axis before the velocity read.

**Wrong "up" axis in pitch math.** `calc_angle` uses `dist_xy` (XY-plane) because Source is
z-up. On a y-up engine the planar distance is over XZ and pitch keys off `delta.y`. Reusing the
z-up form on Unity makes pitch track horizontal distance — aim drifts vertically as the target
strafes.

## See also

- [`common-patterns.md`](common-patterns.md) — the render half (W2S, boxes, radar) and the
  `calc_angle` / `smooth_angle` this file extends.
- [`offset-methodology.md`](offset-methodology.md) — resolving `OFF_VELOCITY`, `OFF_VIEW_ANGLES`,
  `OFF_PUNCH` with sigs instead of hardcodes.
- [`anti-cheat-architecture.md`](anti-cheat-architecture.md) — why instant snaps and memory
  writes are detection surfaces; informs the smoothing and writeback choices above.
- [`pcx-api-cheatsheet.md`](pcx-api-cheatsheet.md) — quick reference for the natives used here.
- [`game-cheat-guidelines`](../.claude/skills/game-cheat-guidelines/SKILL.md) — the 12 rules;
  9 (minimize writes) and 10 (W2S) govern this file directly.
- Perception API: [`proc-api`](../docs/perception/proc-api.md),
  [`render-api`](../docs/perception/render-api.md),
  [`input-api`](../docs/perception/input-api.md),
  [`win-api`](../docs/perception/win-api.md); Enma math:
  [`addon-vec`](../docs/enma/addon-vec.md), [`addon-math`](../docs/enma/addon-math.md).

---

## Source: `knowledge/anti-cheat-architecture.md`

# Kernel Anti-Cheat Architecture Reference

Architecture, components, and detection techniques for major kernel-level anti-cheat systems. Read this before starting AC analysis — it tells you what you're looking at and what each AC is known to monitor.

> **Scope:** Authorized security research only. See `skill://authorized-security-research` before interacting with any live AC system.

---

## Architecture Overview

Every kernel anti-cheat follows the same layered model, with variation in which layers each AC implements:

```
┌──────────────────────────────────────────────────────────┐
│                     Backend Servers                       │
│  (detection rules, telemetry collection, ban decisions)  │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTPS / custom protocol
┌─────────────────────────▼────────────────────────────────┐
│                   AC User-Mode Service                    │
│  (EasyAntiCheat.exe / BEService.exe / vgc.exe)           │
│  Manages driver lifecycle, relays telemetry, heartbeat   │
└──────┬──────────────────┬────────────────────────────────┘
       │ IOCTL / shared   │ injection / pipe
       │ memory / events  │
┌──────▼──────────┐ ┌─────▼─────────────────────────────┐
│  Kernel Driver   │ │  Game-Injected Module              │
│  (.sys)          │ │  (DLL in game process)             │
│  Ring 0          │ │  User-mode integrity, screenshots, │
│  Callbacks,      │ │  in-process scans, heartbeat       │
│  handle strip,   │ └───────────────────────────────────┘
│  system scans    │
└──────────────────┘
```

---

## Per-AC Architecture

### EAC (Easy Anti-Cheat / EOS Anti-Cheat)

| Property | Detail |
|----------|--------|
| **Publisher** | Epic Games (acquired from Kamu, 2018) |
| **Games** | Fortnite, Apex Legends, Rust, Dead by Daylight, The Finals, Hunt: Showdown, Halo MCC, Dark and Darker, many more |
| **User-mode service** | `EasyAntiCheat.exe` (legacy) or `EasyAntiCheat_EOS.exe` (EOS platform) |
| **Game-injected module** | Loaded into game process; performs in-process scans |
| **Kernel driver** | `EasyAntiCheat.sys` or `EasyAntiCheat_EOS.sys` — loaded on demand when game launches, unloaded on exit |
| **Communication** | IOCTL between driver ↔ service; encrypted heartbeat between service ↔ game module; heartbeat failure = game termination |
| **Update mechanism** | Driver is signed; user-mode module updates with game patches; cloud-based detection rules push without client update |
| **Boot behavior** | Loads with the game, not at boot |

**Known driver callbacks:**
- `ObRegisterCallbacks` — strips `PROCESS_VM_READ`/`PROCESS_VM_WRITE` from external handles to the game
- `PsSetCreateProcessNotifyRoutineEx` — monitors process creation
- `PsSetCreateThreadNotifyRoutineEx` — monitors thread creation (injection detection)
- `PsSetLoadImageNotifyRoutine` — monitors module loading
- Minifilter registration — file system monitoring

**Known detection vectors:**
- External process handle with VM access to game
- Module injection into game process (unsigned DLLs)
- Unsigned kernel driver loading
- Hypervisor presence (CPUID checks)
- Debug registers set on game memory
- Code integrity — `.text` section hashing
- Stack anomalies — return addresses outside loaded modules
- Window class/title scanning for known cheat UIs

---

### BattlEye

| Property | Detail |
|----------|--------|
| **Publisher** | BattlEye Innovations (Germany) |
| **Games** | PUBG, R6 Siege, DayZ, Arma 3, Escape from Tarkov, Destiny 2, Fortnite (previously) |
| **User-mode service** | `BEService.exe` — runs as a Windows service |
| **Game-injected module** | `BEClient.dll` / `BEClient_x64.dll` — injected into game process |
| **Kernel driver** | `BEDaisy.sys` — loaded via SCM when game launches |
| **Communication** | Named pipe between service ↔ driver; `BEClient.dll` ↔ `BEService.exe` over local IPC; service ↔ BattlEye backend over HTTPS |
| **Unique** | **BEClient.dll receives shellcode from BattlEye servers at runtime** — detection logic is streamed, not static. This makes static analysis of detection rules nearly impossible. The shellcode runs in the game process context. |
| **Boot behavior** | Loads with the game, not at boot |

**Known driver callbacks:**
- `ObRegisterCallbacks` — handle stripping
- Process, thread, image notification callbacks
- System thread creation for periodic background scans

**Known detection vectors:**
- All of EAC's vectors, plus:
- Window enumeration (`FindWindow` / `EnumWindows` for known cheat tool class names)
- Process name scanning (checks running process names against a list)
- Memory pattern scans inside the game address space (streamed via shellcode)
- Registry key checks for known cheat tool installations
- Driver signing enforcement monitoring

**Analysis difficulty:** HIGH — the streamed shellcode means detection logic changes server-side without any client update. You must capture and analyze the shellcode during a live session.

---

### Vanguard (Riot Games)

| Property | Detail |
|----------|--------|
| **Publisher** | Riot Games |
| **Games** | Valorant, League of Legends (optional) |
| **Kernel driver** | `vgk.sys` — **always-on, loads at boot** |
| **User-mode client** | `vgc.exe` |
| **System tray** | `vgtray.exe` |
| **Boot mechanism** | ELAM (Early Launch Anti-Malware) — loads before third-party drivers, sees everything that loads after it |
| **Requirements** | TPM 2.0, Secure Boot enabled (enforced) |
| **Communication** | Shared memory + fast mutex between `vgk.sys` ↔ `vgc.exe` |
| **Always-on** | Unlike EAC/BE which load with the game, Vanguard runs from boot until manually disabled. Controversial but effective — detects cheat drivers that load before the game. |

**Known driver capabilities:**
- All standard kernel callbacks (process, thread, image, registry, handle)
- Boot-time driver load monitoring (sees every driver that loads)
- Secure Boot chain validation
- TPM attestation
- Hypervisor-level integrity checks
- System integrity verification before allowing game launch

**Analysis difficulty:** VERY HIGH — boot-time loading means snapshot-before-install VM workflow is essential. The ELAM driver loads before most debugging infrastructure.

---

### nProtect GameGuard

| Property | Detail |
|----------|--------|
| **Publisher** | INCA Internet (South Korea) |
| **Games** | MapleStory, Lineage 2, Aion, Black Desert Online, Lost Ark, many Asian MMOs |
| **Components** | GameGuard service, kernel driver (`GameGuard.des` / `GameMon.des` / `GameMon64.des`), game module |
| **Known for** | Aggressive rootkit-like behavior in older versions — SSDT hooks, process hiding, API interception |
| **Legacy behavior** | Older versions hooked the SSDT (System Service Descriptor Table) directly — pre-PatchGuard technique. Modern versions use standard callbacks. |
| **Detection** | Heavy user-mode API hooking in addition to kernel callbacks; monitors clipboard, screenshots, window messages |

---

### XIGNCODE3

| Property | Detail |
|----------|--------|
| **Publisher** | Wellbia.com (South Korea) |
| **Games** | PUBG Mobile (PC emulator), various Asian MMOs and mobile games |
| **Components** | User-mode module + kernel driver |
| **Known for** | Kernel driver + heavy code obfuscation (VMProtect on critical sections), anti-VM checks, timing-based detection |
| **Obfuscation** | Critical driver sections are virtualized with VMProtect — significantly increases analysis difficulty |

---

### Theia (Embark Studios)

| Property | Detail |
|----------|--------|
| **Publisher** | Embark Studios |
| **Games** | The Finals (alongside EAC) |
| **Architecture** | Primarily **server-side** — AI-based behavioral analysis |
| **Components** | Minimal client-side component; heavy server-side telemetry analysis, screenshot capture and AI analysis |
| **Unique** | Focuses on behavioral detection rather than system-level monitoring; runs alongside a traditional AC (EAC) for the system-level layer |

---

## Detection Technique Matrix

Which AC uses which technique (based on public research and analysis):

| Detection Technique | EAC | BattlEye | Vanguard | GameGuard | XIGNCODE3 |
|---|:---:|:---:|:---:|:---:|:---:|
| **Handle stripping** (ObRegisterCallbacks) | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Process creation notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Thread creation notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Image load notify** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Registry callbacks** | ✓ | ✓ | ✓ | ✓ | — |
| **Minifilter (file system)** | ✓ | — | ✓ | ✓ | — |
| **ETW Threat Intelligence** | ✓ | — | ✓ | — | — |
| **Code integrity hashing** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Stack walking** | ✓ | ✓ | ✓ | — | — |
| **Hypervisor detection** | ✓ | ✓ | ✓ | — | ✓ |
| **DMA/IOMMU detection** | ✓ | — | ✓ | — | — |
| **RDTSC timing checks** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Debug register checks** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Module scanning (in-process)** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Window enumeration** | — | ✓ | ✓ | ✓ | — |
| **Streamed detection code** | — | ✓ | — | — | — |
| **Boot-time monitoring** | — | — | ✓ | — | — |
| **TPM / Secure Boot** | — | — | ✓ | — | — |
| **SSDT hooks** (legacy) | — | — | — | ✓ | — |
| **Unsigned driver detection** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Server-side AI analysis** | — | — | — | — | — |

> *Theia omitted — its detection is primarily server-side and not comparable to kernel techniques.*

---

## Anti-Cheat by Game (PCX-Supported Titles)

| Game | Primary AC | Secondary AC | Notes |
|------|-----------|-------------|-------|
| Counter-Strike 2 | VAC | — | Server-side + user-mode; no kernel driver |
| Apex Legends | EAC | — | EOS variant |
| Fortnite | EAC | — | EOS variant |
| PUBG (Steam) | BattlEye | — | `BEDaisy.sys` |
| Escape from Tarkov | BattlEye | — | `BEDaisy.sys` |
| Rainbow Six Siege | BattlEye | — | `BEDaisy.sys` |
| Valorant | Vanguard | — | Boot-time `vgk.sys` |
| The Finals | EAC | Theia | EAC for system-level, Theia for behavioral |
| Dead by Daylight | EAC | — | EOS variant |
| DayZ | BattlEye | — | `BEDaisy.sys` |
| Rust | EAC | — | EOS variant |
| Hunt: Showdown 1896 | EAC | — | EOS variant |
| COD: BO7 / Warzone | RICOCHET | — | Activision's custom kernel AC |
| Overwatch 2 | Custom | — | Blizzard proprietary |
| Deadlock | VAC | — | Server-side |
| Arena Breakout Infinite | EAC | — | EOS variant |
| Marvel Rivals | EAC | — | — |
| Roblox | Byfron (Hyperion) | — | Custom kernel AC (acquired 2022) |

> Games not listed here either use no kernel AC (VAC/server-side only) or use a proprietary solution not publicly documented.

---

## Key Structures Reference

Frequently referenced Windows kernel structures in AC analysis:

```c
// Handle stripping callback context
typedef struct _OB_PRE_OPERATION_INFORMATION {
    OB_OPERATION           Operation;       // OB_OPERATION_HANDLE_CREATE or _DUPLICATE
    union {
        ULONG Flags;
        struct { ULONG KernelHandle:1; ULONG Reserved:31; };
    };
    PVOID                  Object;          // the process/thread being opened
    POBJECT_TYPE           ObjectType;
    PVOID                  CallContext;
    POB_PRE_OPERATION_PARAMETERS Parameters; // contains DesiredAccess to modify
} OB_PRE_OPERATION_INFORMATION;

// The AC's PreOperation callback does:
//   if (target_is_game_process && !opener_is_ac_service)
//       info->Parameters->CreateHandleInformation.DesiredAccess &=
//           ~(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION);
```

```c
// Driver callback arrays in ntoskrnl (symbols):
// PspCreateProcessNotifyRoutine  — array of EX_CALLBACK_ROUTINE_BLOCK pointers
// PspCreateThreadNotifyRoutine   — same
// PspLoadImageNotifyRoutine      — same
// PspCreateProcessNotifyRoutineCount/ExCount — counts
//
// Each entry: pointer with low 4 bits as flags.
// Clear low bits to get the EX_CALLBACK_ROUTINE_BLOCK, then read .Function.
```

---

## Practical Workflow

1. **Identify the AC** — check `game-targets.md` or `system/list_drivers` for known driver names
2. **Read this doc** — understand the AC's known architecture and detection vectors
3. **Follow `skill://anti-cheat-re`** — the six-step methodology
4. **Use `skill://kernel-analysis`** — technical patterns for driver reversing
5. **Refer to `knowledge/kernel-re-tools.md`** — tooling for each workflow stage

---

## Source: `knowledge/cheat-script-cookbook.md`

> **Scope:** Educational cookbook for Perception.cx cheat-script development. Authorized targets only — analyze software you own or have permission to test.

# Cheat Script Cookbook

This file is the practical companion to `game-cheat-guidelines` and `game-hacking-pcx`.
It contains small, reusable recipes for the most common cheat-script tasks. Copy
and adapt them inside your own projects; they follow the 12 guidelines and the
cheat-script master rules.

All examples are written in **Enma (`.em`)**. AngelScript (`.as`) is outside
this toolkit's active support; port old `.as` snippets to Enma before using
these recipes.

---

## Table of Contents

1. [Project skeleton](#project-skeleton)
2. [Process attach + pattern scan](#process-attach--pattern-scan)
3. [Pointer chain walk](#pointer-chain-walk)
4. [World-to-screen](#world-to-screen)
5. [ESP box](#esp-box)
6. [Snapline](#snapline)
7. [Aimbot angle + smoothing](#aimbot-angle--smoothing)
8. [FOV cone check](#fov-cone-check)
9. [Triggerbot](#triggerbot)
10. [Radar](#radar)
11. [Config save/load](#config-saveload)
12. [Unload cleanup](#unload-cleanup)

---

## Project skeleton

```
my_cheat/
├── globals.em    # proc_t, base/size, cache, config
├── offsets.em    # sigs + resolved addresses
├── utils.em      # W2S, distance, team check
├── esp.em        # read + render ESP
├── aim.em        # aimbot logic
├── triggerbot.em # trigger logic
├── radar.em      # 2D radar
├── menu.em       # GUI + config
└── main.em       # setup + routines
```

Compile bundle order: `globals` → `offsets` → `utils` → `esp` → `aim` → `triggerbot`
→ `radar` → `menu` → `main`.

---

## Process attach + pattern scan

```cpp
// main.em
import "globals";
import "offsets";
import "menu";
import "esp";
import "aim";

int64 main() {
    g_proc = ref_process("game.exe");     // set real process name
    if (!g_proc.alive()) {
        println("[main] target not found");
        return 0;
    }

    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0 || g_size == 0) {
        println("[main] module not ready");
        return 0;
    }

    if (!resolve_all()) {
        println("[main] sigs stale");
        return 0;
    }

    setup_menu();
    register_routine(cast<int64>(on_update), 0);  // memory reads
    register_routine(cast<int64>(on_render), 0);  // drawing

    println("[main] loaded");
    return 1;
}
```

```cpp
// offsets.em
import "globals";

const string SIG_ENTITY_LIST = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ??"; // UNVERIFIED
const string SIG_LOCAL_PLAYER = "48 8B 0D ?? ?? ?? ?? 48 85 C9 74 ??"; // UNVERIFIED

uint64 resolve_rip(uint64 hit, int32 disp_off, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = g_proc.r32(hit + cast<uint64>(disp_off));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

bool resolve_all() {
    uint64 hit_el = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit_el == 0) { println("[offsets] entity_list sig stale"); return false; }
    g_entity_list = resolve_rip(hit_el, 3, 7);

    uint64 hit_lp = g_proc.find_code_pattern(g_base, g_size, SIG_LOCAL_PLAYER);
    if (hit_lp == 0) { println("[offsets] local_player sig stale"); return false; }
    g_local_player = resolve_rip(hit_lp, 3, 7);

    return g_entity_list != 0 && g_local_player != 0;
}
```

---

## Pointer chain walk

```cpp
// utils.em
import "globals";

uint64 read_chain(uint64 base, int32[] offsets) {
    uint64 addr = base;
    for (int32 i = 0; i < offsets.length(); i++) {
        if (addr == 0) return 0;
        addr = g_proc.ru64(addr);
        if (addr == 0) return 0;
        addr += cast<uint64>(offsets[i]);
    }
    return addr;
}
```

Usage:

```cpp
int32[] health_chain = { 0x10, 0x20, 0xE8 };
uint64 health_addr = read_chain(g_local_player, health_chain);
if (health_addr == 0) return;
int32 health = g_proc.r32(health_addr);
```

---

## World-to-screen

Source-engine column-major 4x4. Adapt matrix layout for your engine.

```cpp
// utils.em
import "vec";
import "color";
import "globals";

bool world_to_screen(vec3 world, out vec2 screen) {
    float64 m[16];
    // read 16 floats from g_view_matrix (set in offsets.em)
    for (int32 i = 0; i < 16; i++) {
        m[i] = g_proc.rf32(g_view_matrix + cast<uint64>(i * 4));
    }

    float64 w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15];
    if (w < 0.001) return false;

    float64 inv_w = 1.0 / w;
    float64 nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    float64 ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

---

## ESP box

```cpp
// esp.em
import "vec";
import "color";
import "globals";
import "utils";

void esp_update(int64 data) {
    if (!g_esp_enabled || !g_initialized || !g_proc.alive()) return;

    g_esp_count = 0;
    for (int32 i = 0; i < MAX_ENTITIES; i++) {
        uint64 ent = g_proc.ru64(g_entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;
        if (ent == g_local_player) continue;

        EntityInfo info;
        info.pos = g_proc.read_vec3_fl32(ent + OFF_POS);     // verify in IDA
        info.health = g_proc.r32(ent + OFF_HEALTH);
        info.team = g_proc.r32(ent + OFF_TEAM);
        info.valid = true;

        g_entities[g_esp_count] = info;
        g_esp_count++;
        if (g_esp_count >= MAX_ENTITIES) break;
    }
}

void esp_render(int64 data) {
    if (!g_esp_enabled) return;

    color enemy = color(255, 80, 80, 220);
    color ally  = color(80, 255, 80, 220);
    color white = color(255, 255, 255, 255);

    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid) continue;

        vec2 head2d, feet2d;
        vec3 head = e.pos; head.z += 72.0;  // approximate player height
        vec3 feet = e.pos;

        if (!world_to_screen(head, head2d)) continue;
        if (!world_to_screen(feet, feet2d)) continue;

        float64 h = feet2d.y - head2d.y;
        float64 w = h * 0.5;
        color c = (e.team == g_local_team) ? ally : enemy;

        draw_rect(vec2(head2d.x - w*0.5, head2d.y), vec2(w, h), c, 1.0, false);

        string hp_text = format("{}", e.health);
        draw_text(hp_text, vec2(head2d.x - 10.0, head2d.y - 18.0), white,
                  get_font14(), 0, color(0,0,0,0), 0.0);
    }
}
```

---

## Snapline

```cpp
// esp.em (inside esp_render)
vec2 screen_center = vec2(get_view_width() * 0.5, get_view_height());
for (int32 i = 0; i < g_esp_count; i++) {
    EntityInfo e = g_entities[i];
    if (!e.valid) continue;
    vec2 pos;
    if (!world_to_screen(e.pos, pos)) continue;
    draw_line(screen_center, pos, color(255, 255, 255, 120), 1.0);
}
```

---

## Aimbot angle + smoothing

```cpp
// aim.em
import "vec";
import "math";
import "globals";
import "utils";

const float64 PI = 3.14159265358979;
const float64 RAD2DEG = 180.0 / PI;

vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 d = dst.sub(src);
    float64 dist_xy = sqrt(d.x*d.x + d.y*d.y);
    float64 pitch = atan2(-d.z, dist_xy) * RAD2DEG;
    float64 yaw   = atan2(d.y, d.x) * RAD2DEG;
    return vec2(pitch, yaw);
}

float64 normalize_delta(float64 delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}

void aimbot_update(int64 data) {
    if (!g_aim_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_aim_key)) { g_aim_target.valid = false; return; }

    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    vec2 current = read_view_angles();  // engine-specific helper

    EntityInfo best;
    float64 best_score = 1e9;
    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid || e.team == g_local_team || e.health <= 0) continue;

        vec2 target_ang = calc_angle(local_pos, e.pos);
        float64 yaw_delta = normalize_delta(target_ang.y - current.y);
        float64 pitch_delta = fclamp(target_ang.x - current.x, -89.0, 89.0);
        float64 score = yaw_delta*yaw_delta + pitch_delta*pitch_delta;

        if (score < best_score) {
            best_score = score;
            best = e;
        }
    }

    g_aim_target = best;
}

void aimbot_render(int64 data) {
    if (!g_aim_enabled || !g_aim_target.valid) return;

    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    vec2 target = calc_angle(local_pos, g_aim_target.pos);
    vec2 current = read_view_angles();

    float64 yaw_delta   = normalize_delta(target.y - current.y);
    float64 pitch_delta = fclamp(target.x - current.x, -89.0, 89.0);

    vec2 smoothed = vec2(
        current.x + pitch_delta * g_aim_smooth,
        current.y + yaw_delta   * g_aim_smooth
    );

    write_view_angles(smoothed);  // engine-specific helper
}
```

---

## FOV cone check

```cpp
// utils.em
import "math";
import "vec";
import "globals";

vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * (PI / 180.0);
    float64 y = yaw_deg * (PI / 180.0);
    float64 cp = cos(p);
    return vec3(cp * cos(y), cp * sin(y), -sin(p));
}

bool in_fov(vec3 src, vec2 view_angles, vec3 target, float64 fov_deg) {
    vec3 dir = target.sub(src);
    float64 len = sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z);
    if (len == 0.0) return false;
    dir = vec3(dir.x / len, dir.y / len, dir.z / len);

    vec3 fwd = angles_to_forward(view_angles.x, view_angles.y);
    float64 dot = fwd.x*dir.x + fwd.y*dir.y + fwd.z*dir.z;
    return dot >= cos(fov_deg * (PI / 180.0));
}
```

Use it inside `aimbot_update` to filter candidates before scoring.

---

## Triggerbot

```cpp
// triggerbot.em
import "globals";
import "utils";

void triggerbot_update(int64 data) {
    if (!g_trigger_enabled || !g_initialized || !g_proc.alive()) return;
    if (!is_key_down(g_trigger_key)) return;

    EntityInfo crosshair_target = get_entity_under_crosshair(); // engine helper
    if (!crosshair_target.valid) return;
    if (crosshair_target.team == g_local_team) return;
    if (crosshair_target.health <= 0) return;

    // simple fire-rate gate: last fire timestamp
    if (time_ms() - g_last_fire < g_trigger_delay_ms) return;
    g_last_fire = time_ms();

    press_mouse_left();  // or engine-specific fire command
}

void triggerbot_render(int64 data) {
    // nothing to draw; render routine present for registration symmetry
}
```

---

## Radar

```cpp
// radar.em
import "vec";
import "color";
import "globals";

const float64 RADAR_SCALE = 0.05;  // world-units per radar-pixel

void radar_render(int64 data) {
    if (!g_radar_enabled) return;

    vec2 local2d;
    vec3 local_pos = g_proc.read_vec3_fl32(g_local_player + OFF_POS);
    if (!world_to_map(local_pos, local2d)) return;  // project X/Z to 2D

    float64 cx = get_view_width()  - 150.0;
    float64 cy = get_view_height() - 150.0;
    float64 radius = 100.0;

    color bg = color(0, 0, 0, 160);
    draw_circle(vec2(cx, cy), radius, bg, 2.0, true);

    for (int32 i = 0; i < g_esp_count; i++) {
        EntityInfo e = g_entities[i];
        if (!e.valid) continue;

        vec2 blip;
        if (!world_to_map(e.pos, blip)) continue;
        vec2 rel = blip.sub(local2d);
        rel = vec2(rel.x * RADAR_SCALE, rel.y * RADAR_SCALE);
        if (rel.x*rel.x + rel.y*rel.y > radius*radius) continue;

        color c = (e.team == g_local_team) ? color(80,255,80,255) : color(255,80,80,255);
        draw_circle(vec2(cx + rel.x, cy + rel.y), 4.0, c, 1.0, true);
    }
}
```

---

## Config save/load

```cpp
// menu.em
import "json";
import "file";
import "globals";

const string CONFIG_PATH = "my_cheat_config.json";

void save_config() {
    json_value root = json_object();
    root["esp_enabled"] = json_bool(g_esp_enabled);
    root["aim_enabled"] = json_bool(g_aim_enabled);
    root["aim_smooth"]  = json_float(g_aim_smooth);
    root["aim_fov"]     = json_float(g_aim_fov);
    root["trigger_enabled"] = json_bool(g_trigger_enabled);
    root["radar_enabled"]   = json_bool(g_radar_enabled);

    string text = json_stringify(root, 2);
    file_write(CONFIG_PATH, text);
}

void load_config() {
    if (!file_exists(CONFIG_PATH)) return;
    string text = file_read(CONFIG_PATH);
    json_value root = json_parse(text);
    if (root.type() != JSON_OBJECT) return;

    g_esp_enabled     = root["esp_enabled"].as_bool(g_esp_enabled);
    g_aim_enabled     = root["aim_enabled"].as_bool(g_aim_enabled);
    g_aim_smooth      = root["aim_smooth"].as_float(g_aim_smooth);
    g_aim_fov         = root["aim_fov"].as_float(g_aim_fov);
    g_trigger_enabled = root["trigger_enabled"].as_bool(g_trigger_enabled);
    g_radar_enabled   = root["radar_enabled"].as_bool(g_radar_enabled);
}
```

---

## Unload cleanup

```cpp
// main.em
void on_unload() {
    g_initialized = false;
    // no explicit proc_t release in Enma; handle goes out of scope
    println("[main] unloaded");
}
```

For AngelScript, explicitly `deref()` the handle and unregister callbacks.

---

## See Also

- `skill://game-cheat-guidelines` — the 12 hard rules
- `skill://game-hacking-pcx` — full doc index
- `knowledge/aimbot-math.md` — angle math in depth
- `knowledge/common-patterns.md` — W2S, ESP, radar patterns
- `knowledge/offset-methodology.md` — finding and maintaining offsets
- `templates/cheat-skeleton-em/` — full working scaffold

---

## Source: `knowledge/common-patterns.md`

# Common Enma Scripting Patterns for Perception.cx

## Pattern: Process Attach and Module Resolve

```cpp
proc_t g_proc;
uint64 g_base;
uint64 g_size;

bool init_process() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) return false;
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    return g_base != 0;
}
```

## Pattern: Signature Scanning with RIP-Relative Resolution

```cpp
// Resolve a RIP-relative LEA/MOV: instruction at `hit` has a 4-byte displacement at `hit+disp_offset`
// Final address = hit + instruction_length + signed_displacement
uint64 resolve_rip(proc_t& p, uint64 hit, int32 disp_offset, int32 insn_len) {
    if (hit == 0) return 0;
    int32 disp = p.r32(hit + cast<uint64>(disp_offset));
    return hit + cast<uint64>(insn_len) + cast<uint64>(disp);
}

// Example: LEA RCX, [rip+????] = 48 8D 0D ?? ?? ?? ??
// disp_offset=3 (skip 48 8D 0D), insn_len=7
uint64 find_global(proc_t& p, uint64 base, uint64 size, string sig) {
    uint64 hit = p.find_code_pattern(base, size, sig);
    return resolve_rip(p, hit, 3, 7);
}
```

## Pattern: Entity List Iteration with Null Guards

```cpp
void iterate_entities(proc_t& p, uint64 entity_list, int32 max_count) {
    for (int32 i = 0; i < max_count; i++) {
        uint64 ent = p.ru64(entity_list + cast<uint64>(i) * 8);
        if (ent == 0) continue;

        // Read position (Source Engine typically stores as float32 vec3)
        vec3 pos = p.read_vec3_fl32(ent + OFFSET_POSITION);
        int32 health = p.r32(ent + OFFSET_HEALTH);
        int32 team = p.r32(ent + OFFSET_TEAM);

        if (health <= 0) continue;       // skip dead
        if (team == local_team) continue; // skip friendly

        // ... process entity
    }
}
```

## Pattern: World-to-Screen Projection (Source Engine 4x4 Matrix)

```cpp
// Source Engine stores the view-projection matrix as 16 floats (4x4, row-major)
bool world_to_screen(proc_t& p, uint64 matrix_addr, vec3 world, out vec2 screen) {
    // Read the 4 rows (w-component row is row 3)
    float64 w = p.rf32(matrix_addr + 12) * world.x
              + p.rf32(matrix_addr + 28) * world.y
              + p.rf32(matrix_addr + 44) * world.z
              + p.rf32(matrix_addr + 60);

    if (w < 0.001) return false; // behind camera

    float64 inv_w = 1.0 / w;

    float64 nx = (p.rf32(matrix_addr + 0)  * world.x
                + p.rf32(matrix_addr + 16) * world.y
                + p.rf32(matrix_addr + 32) * world.z
                + p.rf32(matrix_addr + 48)) * inv_w;

    float64 ny = (p.rf32(matrix_addr + 4)  * world.x
                + p.rf32(matrix_addr + 20) * world.y
                + p.rf32(matrix_addr + 36) * world.z
                + p.rf32(matrix_addr + 52)) * inv_w;

    float64 vw = get_view_width();
    float64 vh = get_view_height();

    screen = vec2(
        (vw * 0.5) + (nx * vw * 0.5),
        (vh * 0.5) - (ny * vh * 0.5)
    );
    return true;
}
```

## Pattern: 2D Box Overlay with Health Bar

```cpp
import "vec";
import "color";

void draw_entity_box(vec2 head_screen, vec2 feet_screen, float64 health_pct, string name) {
    color c_box = color(255, 50, 50, 200);
    color c_hp  = color(50, 255, 50, 200);
    color c_text = color(255, 255, 255, 255);
    color c_shadow = color(0, 0, 0, 180);

    float64 height = feet_screen.y - head_screen.y;
    float64 width = height * 0.4;
    float64 x = head_screen.x - width * 0.5;
    float64 y = head_screen.y;

    // Box
    draw_rect(vec2(x, y), vec2(width, height), c_box, 1.0, 0.0, 0);

    // Health bar (left side)
    float64 bar_h = height * health_pct;
    float64 bar_y = y + height - bar_h;
    draw_rect_filled(vec2(x - 4.0, bar_y), vec2(2.0, bar_h), c_hp, 0.0, 0);

    // Name text above box
    draw_text(name, vec2(head_screen.x, y - 14.0), c_text, get_font18(), 2, c_shadow, 1.0);
}
```

## Pattern: Snapline Drawing

```cpp
void draw_snapline(vec2 entity_screen) {
    float64 screen_w = get_view_width();
    float64 screen_h = get_view_height();
    vec2 bottom_center = vec2(screen_w * 0.5, screen_h);
    color c = color(255, 255, 255, 120);
    draw_line(bottom_center, entity_screen, c, 1.0);
}
```

## Pattern: Distance Calculation and Display

```cpp
float64 distance_3d(vec3 a, vec3 b) {
    float64 dx = a.x - b.x;
    float64 dy = a.y - b.y;
    float64 dz = a.z - b.z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

void draw_distance(vec2 screen_pos, float64 dist) {
    string text = format("{d}m", cast<int32>(dist / 39.37)); // units to meters
    color white = color(255, 255, 255, 200);
    draw_text(text, vec2(screen_pos.x, screen_pos.y + 12.0), white, get_font18(), 0, color(0,0,0,0), 0.0);
}
```

## Pattern: Angle Calculation (Atan2-Based)

```cpp
vec2 calc_angle(vec3 src, vec3 dst) {
    vec3 delta;
    delta.x = dst.x - src.x;
    delta.y = dst.y - src.y;
    delta.z = dst.z - src.z;
    float64 dist_xy = sqrt(delta.x * delta.x + delta.y * delta.y);
    float64 pitch = atan2(-delta.z, dist_xy) * (180.0 / 3.14159265);
    float64 yaw   = atan2(delta.y, delta.x) * (180.0 / 3.14159265);
    return vec2(pitch, yaw);
}

float64 angle_fov(vec2 current, vec2 target) {
    float64 dp = current.x - target.x;
    float64 dy = current.y - target.y;
    // Normalize yaw delta to [-180, 180]
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return sqrt(dp*dp + dy*dy);
}
```

## Pattern: Smooth Angle Interpolation

```cpp
vec2 smooth_angle(vec2 current, vec2 target, float64 smooth_factor) {
    float64 dx = target.x - current.x;
    float64 dy = target.y - current.y;
    while (dy > 180.0)  dy = dy - 360.0;
    while (dy < -180.0) dy = dy + 360.0;
    return vec2(
        current.x + dx / smooth_factor,
        current.y + dy / smooth_factor
    );
}
```

## Pattern: GUI Menu with Config

```cpp
bool g_enabled = true;
float64 g_max_dist = 3000.0;
float64 g_smooth = 5.0;
int32 g_hotkey = 0x06; // VK_XBUTTON2
color g_color = color(255, 50, 50, 255);

void setup_menu() {
    int64 sec = create_section("Settings");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_dist, 100.0, 10000.0);
    section_slider_float(sec, "Smooth Factor", g_smooth, 1.0, 30.0);
    section_keybind(sec, "Hotkey", g_hotkey);
    section_color_picker(sec, "Overlay Color", g_color);
    section_separator(sec);
    section_label(sec, "v1.0");
}
```

## Pattern: Config Save/Load

```cpp
void save_config() {
    string cfg = "";
    cfg = cfg + "enabled=" + cast<string>(g_enabled) + "\n";
    cfg = cfg + "max_dist=" + cast<string>(g_max_dist) + "\n";
    cfg = cfg + "smooth=" + cast<string>(g_smooth) + "\n";
    write_file("config.txt", cfg);
}

void load_config() {
    if (!file_exists("config.txt")) return;
    string cfg = read_file("config.txt");
    // Parse key=value pairs
    array<string> lines = cfg.split("\n");
    for (string line : lines) {
        array<string> kv = line.split("=");
        if (kv.length() < 2) continue;
        string key = kv[0];
        string val = kv[1];
        if (key == "enabled")  g_enabled = val == "true" || val == "1";
        if (key == "max_dist") g_max_dist = val.to_float();
        if (key == "smooth")   g_smooth = val.to_float();
    }
}
```

## Pattern: Minimap / Radar

```cpp
void draw_radar(vec3 local_pos, float64 local_yaw, vec3[] positions, float64 radar_range) {
    color c_bg    = color(0, 0, 0, 150);
    color c_dot   = color(255, 50, 50, 255);
    color c_self  = color(50, 255, 50, 255);
    float64 radar_size = 150.0;
    float64 cx = 90.0;
    float64 cy = 90.0;

    // Background
    draw_rect_filled(vec2(cx - radar_size*0.5, cy - radar_size*0.5),
                     vec2(radar_size, radar_size), c_bg, 4.0, 15);

    // Self dot at center
    draw_circle(vec2(cx, cy), 3.0, c_self, 1.0, true);

    float64 yaw_rad = local_yaw * (3.14159265 / 180.0);

    for (int32 i = 0; i < positions.length(); i++) {
        float64 dx = positions[i].x - local_pos.x;
        float64 dy = positions[i].y - local_pos.y;

        // Rotate by -yaw so "up" on radar = forward
        float64 rx = dx * cos(-yaw_rad) - dy * sin(-yaw_rad);
        float64 ry = dx * sin(-yaw_rad) + dy * cos(-yaw_rad);

        // Scale to radar
        float64 scale = (radar_size * 0.5) / radar_range;
        float64 px = cx + rx * scale;
        float64 py = cy - ry * scale;

        // Clamp to radar bounds
        float64 half = radar_size * 0.5 - 4.0;
        if (px < cx - half) px = cx - half;
        if (px > cx + half) px = cx + half;
        if (py < cy - half) py = cy - half;
        if (py > cy + half) py = cy + half;

        draw_circle(vec2(px, py), 2.5, c_dot, 1.0, true);
    }
}
```

## Pattern: Complete Script Skeleton

```cpp
import "vec";
import "color";

// Globals
proc_t g_proc;
uint64 g_base;
uint64 g_size;
bool   g_running = false;

// Config (bound to GUI)
bool    g_enabled = true;
float64 g_max_distance = 3000.0;

void on_update(int64 data) {
    if (!g_enabled) return;
    if (!g_proc.alive()) return;
    // ... read game state into cache
}

void on_render(int64 data) {
    if (!g_enabled) return;
    // ... draw from cached state (no proc reads here)
}

int64 main() {
    g_proc = ref_process("game.exe");
    if (!g_proc.alive()) {
        println("Process not found");
        return 0;
    }
    g_base = g_proc.base_address();
    g_size = g_proc.get_module_size("game.exe");
    if (g_base == 0) return 0;

    // Resolve offsets via pattern scans here
    // ...

    // Setup GUI
    int64 sec = create_section("My Script");
    section_checkbox(sec, "Enable", g_enabled);
    section_slider_float(sec, "Max Distance", g_max_distance, 0.0, 10000.0);

    // Register routines
    register_routine(cast<int64>(on_update), 0);
    register_routine(cast<int64>(on_render), 0);

    g_running = true;
    return 1; // stay loaded
}
```

---

## Source: `knowledge/community-tools.md`

# Community Tools & MCP Servers

Third-party tools, MCP servers, VS Code extensions, and utilities built by the Perception.cx community.

---

## MCP Servers

### perception-mcp — by mx13

Full-featured MCP server connecting Claude Code to Perception's RE tools via AngelScript.

**Tools (35+):**
- Memory read/write (typed values, structs, pointer chains, hex dumps)
- IDA-style pattern scanning
- Zydis disassembly
- Function analysis, RTTI, vtable walking
- Full-process value and pointer scanning
- Cross-reference search
- Memory snapshots and diffing
- Unicorn x86_64 emulation
- CS2 interface and schema tools

**Setup:**
```bash
git clone https://github.com/verifizieren/perception-mcp
cd perception-mcp
npm install && npm run build
```

Load `re_server.as` in Perception IDE — it runs in the background and auto-connects.

**MCP Config:**
```json
{
  "mcpServers": {
    "perception-re": {
      "command": "node",
      "args": ["<path-to>/perception-mcp/dist/index.js"]
    }
  }
}
```

**Source:** [github.com/verifizieren/perception-mcp](https://github.com/verifizieren/perception-mcp)

---

### claude-ception — by aewu

Claude Code × Perception MCP bridge for AI-driven live-memory reverse engineering.
Built on ReClass/PerceptionClassEx by segfault and hantschuh.

**Features:**
- Value scans with next-scan filtering
- Pointer-path solving
- Cross-reference sweeps
- Region enumeration and struct reconstruction
- x64 disassembly
- Signature scanning and world-to-screen validation
- AngelScript overlay code generation

**Architecture:**
- `127.0.0.1:9002` — MCP TCP (bridge ↔ plugin, native scans)
- `127.0.0.1:9001` — WebSocket memory reads via Perception

**Setup:**
```
perception-claude-bundle/
├─ README-BUNDLE.md     - quick start
├─ system-prompt.md     - RE system prompt
├─ pclaude.cmd          - launches Claude Code with prompt
├─ .mcp.json            - MCP server registration
├─ reclass-mcp/         - MCP bridge (Node.js)
├─ PCX-runtime/         - ready-to-run exe + plugin + .as script
└─ PCX-src/             - full source (editor + plugin)
```

**Requirements:** Node.js 18+, Claude Code CLI.

**Source:** Available on perception.cx forums (Learning & Research section).

---

### reclass-mcp — by hantschuh

The original ReClass MCP bridge for Claude Code — the foundation claude-ception builds on.

**Features:**
- Memory read/write through PerceptionClassEx
- Pattern scanning
- Struct reconstruction
- Pointer chain resolution

**Source:** Available on perception.cx forums.

---

### Unreal Engine Documentation MCP — by jozkah

MCP server providing direct access to official Unreal Engine documentation with version selection (UE 4.27 — 5.7).

**Tools:**
- `search` — keyword search across all UE docs
- `read_page` — fetch any doc page as clean markdown
- `browse_categories` — list top-level doc sections
- `cpp_api_lookup` — look up classes, structs, functions (AActor, FVector, UObject, etc.)

**Setup:**
```bash
git clone https://github.com/Jozkah/Unreal-Engine-Documentation-MCP.git
cd Unreal-Engine-Documentation-MCP
npm install && npm run build
```

**MCP Config (VS Code):**
```json
{
  "servers": {
    "unreal-engine-docs": {
      "command": "node",
      "args": ["<path>/Unreal-Engine-Documentation-MCP/dist/index.js"]
    }
  }
}
```

No API keys needed — reads public documentation. MIT licensed.

**Source:** [github.com/Jozkah/Unreal-Engine-Documentation-MCP](https://github.com/Jozkah/Unreal-Engine-Documentation-MCP)

---

### Context7 Integration

Hosted MCP server (by Upstash) that indexes official documentation for thousands of libraries with version pinning.

**Relevant Indexed Content:**
- Unreal Engine 5.7 — 80,411 code snippets
- Unity Manual — 47,581 snippets
- Godot Engine 4.5/4.6 — ~20k snippets each
- Ghidra API — 80,664 snippets
- IDA SDK — 535 snippets

**Setup:**
```bash
npx ctx7 setup --claude     # Claude Code
npx ctx7 setup --cursor     # Cursor
```

**Manual MCP Config:**
```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": { "CONTEXT7_API_KEY": "your-key-here" }
    }
  }
}
```

Free tier available (rate-limited). Get an API key at `context7.com/dashboard`.

**Source:** [context7.com](https://context7.com)

---

## VS Code Extensions

### Enma LSP — by sin (sinnafuls)

Full-featured VS Code extension for Enma scripting with Perception integration.

**Features:**
- **IntelliSense** — autocompletion for all Perception globals, classes, structs, methods, and Enma stdlib
- **Hover docs** — signatures and descriptions for every function
- **Parameter hints** — active parameter highlighting
- **Go-to-definition** — `Ctrl+Click` any symbol
- **Find references** — across entire project (including f-string interpolations)
- **Safe rename** — across all files
- **Workspace symbol search** — `Ctrl+T`
- **Type-mismatch diagnostics** — real-time error checking
- **Quick-fix imports** — auto-insert missing `import "vec"` etc.

**Bundler:**
- `Ctrl+Alt+B` — bundle `#include`-split project into single `.em`
- `Ctrl+Alt+Shift+B` — bundle and strip comments
- Auto-rebundle on save (configurable)
- Multi-project support

**Engine MCP Client:**
- Run script via MCP (`script/execute`)
- Validate on save (`script/validate`)
- Configurable endpoint (default `http://127.0.0.1:9077/mcp`)

**DAP Debugger:**
- Attach to running Enma DAP server (`F5`, default `localhost:27979`)
- Breakpoints in `.em` files

**Project Commands:**
- `Enma: Initialize Project` — scaffold `source/main.em` + tasks.json
- `Enma: Scaffold From Template…` — `perception-minimal` or `perception-multi`
- `Enma: Generate CI Workflow` — `.github/workflows/enma.yml`

**Install:** Download `.vsix` from [GitHub Releases](https://github.com/sinnafuls/enma-lsp/releases), then `Ctrl+Shift+P` → "Extensions: Install from VSIX…"

**Source:** [github.com/sinnafuls/enma-lsp](https://github.com/sinnafuls/enma-lsp)

---

### AngelScript LSP + Bundler — by Shadow / sin

AngelScript language server with Perception-specific extensions.

**Features:**
- Syntax highlighting and diagnostics
- IntelliSense for PCX AngelScript API
- Script bundling and validation

---

### VS Perception Extension — by banjo

VS Code extension for Perception development workflow.

---

## Utilities

### Claude Proxy — by sin (sinistercodes)

Proxy server that routes Claude API requests to Perception's IDE chatbot.

**Setup:**
```bash
git clone https://github.com/sinistercodes/claude-proxy
cd claude-proxy
npm install
cp .env.example .env  # configure model/thinking budget
node --env-file=.env server.js
```

**Perception IDE Config:**
- Base URL: `http://localhost:4001/v1/chat/completions`
- API key: any string
- Model: sonnet, opus, or haiku

**Source:** [github.com/sinistercodes/claude-proxy](https://github.com/sinistercodes/claude-proxy)

---

### AngelScript Custom GUI + Base — by underscore

Open-source full GUI system and script base for AngelScript.

**Includes:**
- Full custom menu/GUI — windows, tabs, containers
- All widget types: checkboxes, sliders, keybinds, dropdowns, multi-selects, color pickers, list boxes, text inputs, tooltips, labels, buttons
- Config & theme systems with save/load
- Notifications and draggable HUD widgets
- Attachment system — process memory I/O, pattern scanning, UE FString/FText/vector/matrix/quaternion helpers
- Threading/callback system with perf timing

Full API docs in the README. Fork and build on top of it.

**Source:** Available on perception.cx forums (Learning & Research section).

---

### dumpception — by sin

SDK/offset dumping utility for Perception.

---

### Universal Offset Scanner — by ItachiValor

Automated offset discovery tool (private beta).

Available on perception.cx Script Market.

---

## Kernel RE & Anti-Cheat Analysis Tools

Tools for kernel driver analysis and anti-cheat reverse engineering. Full reference with platform matrix and workflow: `knowledge/kernel-re-tools.md`.

### HyperDbg

Hypervisor-level debugger — sits below the OS, invisible to kernel anti-debug. Stealth breakpoints, EPT hooks, syscall interception. The only debugger an AC's kernel-mode anti-debug can't detect via standard means.

**Source:** [github.com/HyperDbg/HyperDbg](https://github.com/HyperDbg/HyperDbg)

---

### Volatility 3

Memory forensics framework. Analyze physical memory dumps: driver lists (`windows.driverscan`), callback arrays (`windows.callbacks`), handle tables, process trees. Essential for offline AC driver analysis.

**Install:** `pip install volatility3`
**Source:** [github.com/volatilityfoundation/volatility3](https://github.com/volatilityfoundation/volatility3)

---

### MemProcFS

Mount a physical memory dump (or live DMA feed via PCILeech) as a virtual filesystem. Browse processes, modules, registry, network connections as files. Integrates with PCILeech for live DMA-based analysis invisible to software ACs.

**Source:** [github.com/ufrisk/MemProcFS](https://github.com/ufrisk/MemProcFS)

---

### IRPMon

Intercepts IRP (I/O Request Packets) to/from kernel drivers. Capture IOCTL traffic between the AC user-mode service and kernel driver — see the protocol in real time.

**Source:** [github.com/MartinDrab/IRPMon](https://github.com/MartinDrab/IRPMon)

---

### VirtualKD-Redux

Patches the VM's `kdcom.dll` to use a fast pipe instead of serial — 10–40× faster kernel debugging in VMware/VirtualBox. Use with WinDbg for practical-speed kernel debug sessions.

**Source:** [github.com/4d61726b/VirtualKD-Redux](https://github.com/4d61726b/VirtualKD-Redux)

---

### PCILeech

DMA-based memory acquisition via FPGA or Thunderbolt. Reads physical memory without software on the target — completely invisible to software-based ACs. Requires FPGA hardware (Screamer, LambdaConcept) or Thunderbolt access.

**Source:** [github.com/ufrisk/pcileech](https://github.com/ufrisk/pcileech)

---

## Source: `knowledge/custom-draw-patterns.md`

# Custom Draw API Patterns for Perception.cx

Direct D3D11 GPU access from AngelScript/Enma. Write HLSL shaders, create
vertex/index/constant buffers, textures, render targets, and depth buffers,
then draw with any primitive topology. Custom draw commands respect draw
order with every existing render function.

> Resource creators return a `uint64` handle (`0` on failure). All resources
> are tracked per-script and auto-cleaned on script unload, so you create them
> once and reuse the handles every frame.

## Pattern: Basic 2D Colored Shape with Shader

Use case: a custom-shaded overlay primitive (gradient triangle, FOV wedge,
crosshair quad) that the built-in `draw_*` helpers can't express. Demonstrates
the minimal shader + vertex buffer + draw-call loop.

```cpp
// --- HLSL: vertex shader transforms 2D screen-space pos by an ortho matrix ---
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj); // 2D -> clip space
    o.col = i.col;
    return o;
}
""";

// --- HLSL: pixel shader just passes the interpolated vertex color ---
string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

// Created ONCE (e.g. in on_load), reused every frame
uint64 g_shader = 0;
uint64 g_vb     = 0;
uint64 g_blend  = 0;

void cd_init_shape() {
    // layout: POSITION = float2, COLOR = float4 -> 24-byte stride
    g_shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
    g_vb     = create_vertex_buffer(24, 3, true); // stride, max verts, dynamic
    g_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_shape(float4x4 ortho) {
    // Interleaved vertex data: 3 verts x (pos.xy, col.rgba)
    array<float> verts = {
        100.0, 100.0,  1.0, 0.0, 0.0, 1.0,   // red
        300.0, 100.0,  0.0, 1.0, 0.0, 1.0,   // green
        200.0, 300.0,  0.0, 0.0, 1.0, 1.0    // blue
    };
    // proj matrix goes into constant buffer slot b0
    array<float> cb_data = ortho.to_array();

    custom_draw(g_shader, g_vb, verts, 3, TOPO_TRIANGLE_LIST,
                g_blend, 0, 0,        // no sampler/texture for solid color
                0,                    // rt=0 -> draw to backbuffer
                0, cb_data, 0);       // cb auto-managed, data, slot b0
}
```

## Pattern: Textured Quad with Custom Texture

Use case: render a logo, sprite sheet, watermark, or a CPU-generated image
onto a screen-space quad. Loads a texture, binds a sampler, and samples it in
the pixel shader.

```cpp
string vs_tex = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float2 uv : TEXCOORD; };
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.uv  = i.uv;
    return o;
}
""";

string ps_tex = """
Texture2D    tex : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return tex.Sample(smp, i.uv); }
""";

uint64 g_tex_shader = 0;
uint64 g_tex_vb     = 0;
uint64 g_tex        = 0;
uint64 g_sampler    = 0;
uint64 g_tex_blend  = 0;

void cd_init_textured() {
    g_tex_shader = create_shader(vs_tex, ps_tex, "POSITION:0:FLOAT2, TEXCOORD:0:FLOAT2");
    g_tex_vb     = create_vertex_buffer(16, 6, true);  // float2 pos + float2 uv = 16 bytes
    g_tex        = create_texture_from_file("logo.png"); // RGBA from disk
    g_sampler    = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_tex_blend  = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                      BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
}

void cd_draw_textured(float4x4 ortho, float64 x, float64 y, float64 w, float64 h) {
    float fx = float(x); float fy = float(y);
    float fw = float(w); float fh = float(h);
    // Two triangles forming a quad: (pos.xy, uv.xy)
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_tex, // bind sampler + texture
                0, 0, cb_data, 0);
}
```

## Pattern: 3D Cube with Depth Testing

Use case: render a true 3D object (debug box, chams cage, world marker) that
correctly occludes itself. Uses an index buffer to share cube corners, a
depth buffer, and a depth-stencil state with `CMP_LESS`.

```cpp
string vs_3d = """
cbuffer cb : register(b0) { float4x4 mvp; };
struct VS_IN  { float3 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 1), mvp); // model-view-projection
    o.col = i.col;
    return o;
}
""";

string ps_3d = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 g_cube_shader = 0;
uint64 g_cube_vb     = 0;
uint64 g_cube_ib     = 0;
uint64 g_depth_buf   = 0;
uint64 g_ds_state    = 0;
uint64 g_cube_blend  = 0;

void cd_init_cube(int32 vw, int32 vh) {
    g_cube_shader = create_shader(vs_3d, ps_3d, "POSITION:0:FLOAT3, COLOR:0:FLOAT4");
    g_cube_vb     = create_vertex_buffer(28, 8, false);   // float3 pos + float4 col = 28 bytes, 8 corners
    g_cube_ib     = create_index_buffer(36, false, false); // 12 tris * 3 = 36 indices, 16-bit
    g_depth_buf   = create_depth_buffer(vw, vh);
    g_ds_state    = create_depth_stencil_state(true, true, CMP_LESS); // depth on, write on
    g_cube_blend  = create_blend_state(BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD,
                                       BLEND_ONE, BLEND_ZERO, BLEND_OP_ADD); // opaque
}

void cd_draw_cube(float4x4 mvp, int32 vw, int32 vh) {
    // 8 cube corners: (pos.xyz, col.rgba)
    array<float> verts = {
        -1,-1,-1, 1,0,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,0,1,1,  -1, 1,-1, 1,1,0,1,
        -1,-1, 1, 1,0,1,1,   1,-1, 1, 0,1,1,1,
         1, 1, 1, 1,1,1,1,  -1, 1, 1, 0,0,0,1
    };
    // 12 triangles (two per face), CCW winding
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,   // back, front
        4,5,1, 4,1,0,   3,2,6, 3,6,7,   // bottom, top
        1,5,6, 1,6,2,   4,0,3, 4,3,7    // right, left
    };
    array<float> cb_data = mvp.to_array();

    // Bind a depth-enabled render target + clear it, then set depth state
    custom_set_render_target_ext(0, g_depth_buf); // 0 = backbuffer color
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);
}
```

## Pattern: Wireframe Rendering

Use case: debug visualization of geometry, hitbox cages, or a "skeleton"
look. Identical geometry path as the solid cube but with a rasterizer state
set to `FILL_WIREFRAME` so only triangle edges are drawn.

```cpp
// Reuses g_cube_shader / g_cube_vb / g_cube_ib / g_depth_buf from the 3D cube pattern.
uint64 g_rs_wire  = 0;
uint64 g_rs_solid = 0;

void cd_init_wireframe() {
    // Wireframe + no culling so back edges are visible too
    g_rs_wire  = create_rasterizer_state(FILL_WIREFRAME, CULL_NONE);
    g_rs_solid = create_rasterizer_state(FILL_SOLID, CULL_BACK); // to restore afterwards
}

void cd_draw_wireframe(float4x4 mvp, int32 vw, int32 vh) {
    array<float> verts = {
        -1,-1,-1, 0,1,0,1,   1,-1,-1, 0,1,0,1,
         1, 1,-1, 0,1,0,1,  -1, 1,-1, 0,1,0,1,
        -1,-1, 1, 0,1,0,1,   1,-1, 1, 0,1,0,1,
         1, 1, 1, 0,1,0,1,  -1, 1, 1, 0,1,0,1
    };
    array<uint16> indices = {
        0,1,2, 0,2,3,   4,6,5, 4,7,6,
        4,5,1, 4,1,0,   3,2,6, 3,6,7,
        1,5,6, 1,6,2,   4,0,3, 4,3,7
    };
    array<float> cb_data = mvp.to_array();

    custom_set_render_target_ext(0, g_depth_buf);
    custom_clear_depth_buffer(g_depth_buf);
    custom_set_depth_stencil_state(g_ds_state);
    custom_set_rasterizer_state(g_rs_wire);  // <-- switch to wireframe fill
    custom_set_viewport(0, 0, vw, vh);

    custom_draw_indexed(g_cube_shader, g_cube_vb, verts, 28,
                        g_cube_ib, indices, 36, TOPO_TRIANGLE_LIST,
                        g_cube_blend, 0, 0, 0, 0, cb_data, 0);

    custom_set_rasterizer_state(g_rs_solid); // restore so later draws are solid
}
```

## Pattern: Glow / Blur Post-Processing

Use case: a soft glow around overlay elements or a bloom effect. Render the
source into an off-screen render target, run a separable blur pass that
samples the RT, then composite the blurred result back over the backbuffer
with additive blending.

```cpp
// Fullscreen-triangle vertex shader (no vertex buffer needed; uses SV_VertexID)
string vs_fs = """
struct VS_OUT { float4 pos : SV_Position; float2 uv : TEXCOORD; };
VS_OUT main(uint id : SV_VertexID) {
    VS_OUT o;
    o.uv  = float2((id << 1) & 2, id & 2);            // 0,0 / 2,0 / 0,2
    o.pos = float4(o.uv * float2(2, -2) + float2(-1, 1), 0, 1);
    return o;
}
""";

// Separable Gaussian blur; direction passed via constant buffer (1,0)=horiz, (0,1)=vert
string ps_blur = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
cbuffer cb : register(b0) { float2 dir; float2 texel; };
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float w[5] = { 0.227, 0.194, 0.121, 0.054, 0.016 };
    float4 c = src.Sample(smp, i.uv) * w[0];
    for (int k = 1; k < 5; k++) {
        float2 off = dir * texel * k;
        c += src.Sample(smp, i.uv + off) * w[k];
        c += src.Sample(smp, i.uv - off) * w[k];
    }
    return c;
}
""";

// Additive composite of blurred RT over the backbuffer
string ps_composite = """
Texture2D    src : register(t0);
SamplerState smp : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target { return src.Sample(smp, i.uv); }
""";

uint64 g_blur_shader = 0;
uint64 g_comp_shader = 0;
uint64 g_rt_a = 0;
uint64 g_rt_b = 0;
uint64 g_blur_smp   = 0;
uint64 g_add_blend  = 0;
int32  g_rt_w = 0;
int32  g_rt_h = 0;

void cd_init_glow(int32 w, int32 h) {
    g_rt_w = w; g_rt_h = h;
    g_blur_shader = create_shader(vs_fs, ps_blur, "");       // no input layout
    g_comp_shader = create_shader(vs_fs, ps_composite, "");
    g_rt_a = create_render_target(w, h);  // ping
    g_rt_b = create_render_target(w, h);  // pong
    g_blur_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
    g_add_blend = create_blend_state(BLEND_ONE, BLEND_ONE, BLEND_OP_ADD, // additive
                                     BLEND_ONE, BLEND_ONE, BLEND_OP_ADD);
}

// `source_tex` is what you want to glow (e.g. a captured/rendered RT texture)
void cd_draw_glow(uint64 source_tex) {
    float tx = 1.0 / float(g_rt_w);
    float ty = 1.0 / float(g_rt_h);

    // Pass 1: horizontal blur, source_tex -> rt_a
    array<float> cb_h = { 1.0, 0.0, tx, ty };
    custom_clear_render_target(g_rt_a, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, source_tex, g_rt_a, 0, cb_h, 0);

    // Pass 2: vertical blur, rt_a -> rt_b
    array<float> cb_v = { 0.0, 1.0, tx, ty };
    custom_clear_render_target(g_rt_b, 0, 0, 0, 0);
    custom_draw(g_blur_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_blur_smp, g_rt_a, g_rt_b, 0, cb_v, 0);

    // Pass 3: composite blurred rt_b additively onto the backbuffer (rt=0)
    custom_draw(g_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                g_add_blend, g_blur_smp, g_rt_b, 0, 0, array<float>(), 0);
}
```

## Pattern: Compute Shader Data Processing

Use case: offload heavy per-element math to the GPU — batch world-to-screen
projection, particle simulation, or bulk distance/visibility checks. Creates
a compute shader, a structured buffer of input/output data, dispatches thread
groups, then reads the results back to the CPU.

```cpp
// Compute shader: multiplies every element by 2 (stand-in for real batch work)
string cs = """
RWStructuredBuffer<float> data : register(u0);
[numthreads(64, 1, 1)]
void main(uint3 id : SV_DispatchThreadID) {
    data[id.x] = data[id.x] * 2.0;
}
""";

uint64 g_compute = 0;

void cd_init_compute() {
    g_compute = create_compute_shader(cs);
}

array<float> cd_run_compute(array<float> input) {
    uint element_count = input.length();

    // 4-byte float elements; upload initial data
    uint64 buf = create_structured_buffer(4, element_count, input);

    // Each group handles 64 elements (matches numthreads); round up
    uint groups = (element_count + 63) / 64;
    dispatch_compute(g_compute, groups, 1, 1);

    // Read processed data back into an AngelScript array
    array<float> result = read_structured_buffer(buf);
    return result; // each element doubled
}
```

## Pattern: Multi-Pass Rendering with Multiple Render Targets

Use case: composing a final image from several layers — e.g. render solid
geometry to one RT, an outline/mask to another, then combine both in a final
fullscreen pass. Demonstrates rendering into separate targets and sampling
multiple textures in the composite shader.

```cpp
// Final composite samples two render-target textures and blends them
string ps_mrt_composite = """
Texture2D    sceneTex : register(t0);
Texture2D    maskTex  : register(t1);
SamplerState smp      : register(s0);
struct PS_IN { float4 pos : SV_Position; float2 uv : TEXCOORD; };
float4 main(PS_IN i) : SV_Target {
    float4 scene = sceneTex.Sample(smp, i.uv);
    float  mask  = maskTex.Sample(smp, i.uv).r;
    // Tint the masked region (outline) cyan, leave the rest as the scene
    float3 outline = float3(0, 1, 1) * mask;
    return float4(scene.rgb + outline, 1);
}
""";

uint64 g_mrt_comp_shader = 0;
uint64 g_rt_scene = 0;
uint64 g_rt_mask  = 0;
uint64 g_mrt_smp  = 0;

void cd_init_mrt(int32 w, int32 h) {
    g_mrt_comp_shader = create_shader(vs_fs, ps_mrt_composite, ""); // reuse fullscreen VS
    g_rt_scene = create_render_target(w, h);
    g_rt_mask  = create_render_target(w, h);
    g_mrt_smp  = create_sampler(FILTER_LINEAR, ADDRESS_CLAMP, ADDRESS_CLAMP);
}

void cd_draw_mrt(float4x4 mvp, array<float> scene_verts, array<float> mask_verts) {
    array<float> cb = mvp.to_array();

    // Pass 1: render the scene geometry into g_rt_scene
    custom_clear_render_target(g_rt_scene, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, scene_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_scene, 0, cb, 0);

    // Pass 2: render the mask/outline geometry into g_rt_mask
    custom_clear_render_target(g_rt_mask, 0, 0, 0, 1);
    custom_draw(g_cube_shader, g_cube_vb, mask_verts, 3, TOPO_TRIANGLE_LIST,
                g_cube_blend, 0, 0, g_rt_mask, 0, cb, 0);

    // Pass 3: composite both RTs onto the backbuffer.
    // custom_bind_textures binds extra texture slots (t0, t1, ...) for one shader.
    custom_bind_textures(g_mrt_comp_shader, g_rt_scene, g_rt_mask);
    custom_draw(g_mrt_comp_shader, 0, array<float>(), 3, TOPO_TRIANGLE_LIST,
                0, g_mrt_smp, g_rt_scene, 0, 0, array<float>(), 0);
}
```

## Pattern: Dynamic Texture Update

Use case: a CPU-generated image that changes every frame — a software-drawn
minimap, a spectrogram, a heatmap, or scrolling text. Create a dynamic
texture once, rewrite its RGBA pixel buffer each frame, then draw it with the
textured-quad path.

```cpp
// Reuses g_tex_shader / g_tex_vb / g_sampler / g_tex_blend from the textured-quad pattern.
uint64 g_dyn_tex = 0;
int32  g_dyn_w = 256;
int32  g_dyn_h = 256;

void cd_init_dynamic() {
    g_dyn_tex = create_dynamic_texture(g_dyn_w, g_dyn_h); // allocated once
}

// Builds a fresh RGBA8 buffer and uploads it. `t` animates the pattern.
void cd_update_dynamic(float64 t) {
    array<uint8> pixels(g_dyn_w * g_dyn_h * 4); // 4 bytes per pixel (RGBA)

    for (int32 y = 0; y < g_dyn_h; y++) {
        for (int32 x = 0; x < g_dyn_w; x++) {
            int32 idx = (y * g_dyn_w + x) * 4;
            // Simple animated plasma so the update is visible per-frame
            uint8 r = uint8((sin(x * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 g = uint8((sin(y * 0.05 + t) * 0.5 + 0.5) * 255.0);
            uint8 b = uint8((sin((x + y) * 0.05 + t) * 0.5 + 0.5) * 255.0);
            pixels[idx + 0] = r;
            pixels[idx + 1] = g;
            pixels[idx + 2] = b;
            pixels[idx + 3] = 255; // opaque
        }
    }

    update_dynamic_texture(g_dyn_tex, pixels); // re-upload to GPU
}

void cd_draw_dynamic(float4x4 ortho, float64 x, float64 y) {
    float fx = float(x); float fy = float(y);
    float fw = float(g_dyn_w); float fh = float(g_dyn_h);
    array<float> verts = {
        fx,      fy,      0.0, 0.0,
        fx + fw, fy,      1.0, 0.0,
        fx,      fy + fh, 0.0, 1.0,
        fx + fw, fy,      1.0, 0.0,
        fx + fw, fy + fh, 1.0, 1.0,
        fx,      fy + fh, 0.0, 1.0
    };
    array<float> cb_data = ortho.to_array();

    custom_draw(g_tex_shader, g_tex_vb, verts, 6, TOPO_TRIANGLE_LIST,
                g_tex_blend, g_sampler, g_dyn_tex, // bind the dynamic texture
                0, 0, cb_data, 0);
}
```

---

## Source: `knowledge/deobfuscation-tools.md`

# Deobfuscation Tools Reference

Tools for defeating binary protection: devirtualizers, unpackers, symbolic execution engines, anti-debug bypass, string extraction, and CFG recovery. Organized by the obfuscation layer they target.

> **Scope:** Authorized security research only. These tools are for analyzing binaries you own, are authorized to test, or are studying in a research/CTF context. See `skill://authorized-security-research`.

---

## Devirtualizers (VM → native/IR)

| Tool | Target VM | Output | Status |
|------|-----------|--------|--------|
| **backengineering/vmp2** (`vmemu` / `vmdevirt` / `vmprofiler`) | VMProtect 2.x | Unpacked memory / lifted IR / handler stats | Active; full VMP 2.x research toolchain |
| **NoVmp** | VMProtect 3.x | LLVM IR → x86 | Active; best open-source VMP 3.x devirtualizer |
| **VMHunt** | VMProtect | Expression trees | Research; trace-based handler semantic extraction |
| **vtil** (Virtual-machine Translation IL) | VMProtect, generic | VTIL IR → optimized | Active; VTIL is a dedicated IR for VM lifting |
| **Oreans UnVirtualizer** | Themida/CV (older) | x86 | Limited on newer versions |
| **Devirtualize** (can1357) | VMProtect 2.x | Lifted IR | Older; VMP 2.x only |
| **VMPAttack** | VMProtect 3.x | Trace analysis | Trace + symbolic; less automated than NoVmp |

### NoVmp — VMProtect Devirtualizer

**What:** Static devirtualizer for VMProtect. Analyzes the VM dispatcher and handler table, identifies the VM architecture, lifts the bytecode to LLVM IR, optimizes it, and optionally recompiles to x86.

**Install:**
```bash
git clone https://github.com/can1357/NoVmp.git
cd NoVmp && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

**Usage:**
```bash
# Lift a VMP-protected function at RVA 0x1234
novmp --input protected.exe --rva 0x1234 --output lifted.ll
# The output is LLVM IR — readable with llvm-dis or optimizable with opt
opt -O2 lifted.ll -o optimized.ll
```

**Source:** [github.com/can1357/NoVmp](https://github.com/can1357/NoVmp)

---

### backengineering/vmp2 — VMProtect 2.x Research Suite

**What:** A complete open-source research toolchain for VMProtect 2.x. `vmemu`
unpacks the protected binary by emulating the VM runtime; `vmdevirt` lifts the
VM bytecode closer to native code; `vmprofiler`/`vmprofiler-cli` profile
handler coverage; `vmhook` captures bytecode streams at runtime; `vmassembler`
assembles/disassembles VMP bytecode.

**Install:**
```bash
git clone https://github.com/backengineering/vmp2.git
cd vmp2
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

**Usage:**
```bash
# Unpack to an image
vmemu --bin target.exe --unpack --out unpacked.bin

# Lift a VM bytecode region
vmdevirt --input target.exe --bytecode-rva 0x12345 --output lifted.asm

# Profile handler coverage
vmprofiler-cli --input target.exe --trace trace.txt --output report.json
```

**Workflow:** see `knowledge/vmprotect2-analysis.md` for the full
identify → bypass anti-debug → unpack → lift → validate workflow.

**Source:** [github.com/backengineering/vmp2](https://github.com/backengineering/vmp2)

---

### vtil — VM Translation IL

**What:** A dedicated intermediate language and optimizer for representing VM-lifted code. Designed specifically for the operations VMs perform (push/pop, handler dispatch, virtual register access). More appropriate than LLVM IR for VM analysis because it preserves VM semantics during optimization.

**Source:** [github.com/vtil-project/VTIL-Core](https://github.com/vtil-project/VTIL-Core)

---

## Symbolic Execution Engines

| Tool | Language | Best For |
|------|----------|----------|
| **Triton** | C++ / Python bindings | Precise symbolic execution, constraint solving, taint analysis |
| **Miasm** | Python | IR lifting, symbolic execution, code emulation, CFG recovery |
| **angr** | Python | Full binary analysis framework; symbolic execution + CFG recovery |
| **Unicorn Engine** | C / Python | CPU emulation (not symbolic); trace concrete execution |
| **Qiling** | Python | Higher-level emulation framework built on Unicorn; OS emulation |

### Triton — Dynamic Symbolic Execution

**What:** Pin-based dynamic symbolic execution engine. Hooks instruction execution, builds symbolic expressions for each operation, and can solve constraints (via Z3) to find inputs that reach specific code paths.

**Use for:**
- Evaluating opaque predicates (prove a branch is always-true/always-false)
- Simplifying MBA expressions (`(x ^ y) + 2*(x & y)` → `x + y`)
- Tracing VM handler semantics symbolically
- Deobfuscating control flow by resolving indirect branches

**Install:**
```bash
pip install triton-library
# Or build from source for Pin integration:
git clone https://github.com/JonathanSalwan/Triton.git
```

**Source:** [github.com/JonathanSalwan/Triton](https://github.com/JonathanSalwan/Triton)

---

### Miasm — Reverse Engineering Framework

**What:** Full RE framework with its own IR (Miasm IR), symbolic execution, code emulation, and binary analysis. Particularly strong at lifting x86 to IR and performing transformations (dead code elimination, constant propagation).

**Use for:**
- Lifting x86 instruction traces to a clean IR
- Dead code / junk code elimination via dataflow analysis
- Automated deobfuscation pipelines (script a chain: lift → simplify → emit)
- Handling self-modifying code (emulate the modification, then analyze the result)

**Install:**
```bash
pip install miasm
```

**Source:** [github.com/cea-sec/miasm](https://github.com/cea-sec/miasm)

---

## IDA Pro Plugins

### D-810 — Deobfuscation Plugin

**What:** IDA plugin for deobfuscating code at the microcode level. Handles CFF recovery, opaque predicate removal, MBA simplification, and dead code elimination. Works on IDA's internal microcode representation, so results appear directly in the decompiler output.

**Handles:**
- OLLVM/Hikari control flow flattening
- Opaque predicates (constant-condition branches)
- Instruction substitution patterns
- MBA (Mixed Boolean-Arithmetic) expression simplification
- Dead code paths

**Install:** Copy plugin to IDA plugins directory. Requires IDA 7.4+ with Hex-Rays decompiler.

**Source:** [github.com/joydo/d-810](https://github.com/joydo/d-810)

---

### hrtng — Deobfuscation & Decryption (already installed)

2024 Hex-Rays Plugin Contest winner. Handles string decryption, control flow unflattening, vtable resolution. Already in `re-tools/ida-plugins/hrtng/`.

---

### HashDB — API Hash Resolver

**What:** Resolves API hashes used by malware and protectors for dynamic import resolution. Supports 50+ hash algorithms (ROR13+ADD, CRC32, DJB2, FNV-1a, MurmurHash, etc.). Identifies the algorithm and resolves the hash to the API name.

**Source:** [github.com/OALabs/hashdb-ida](https://github.com/OALabs/hashdb-ida)

---

## Binary Ninja Plugins

### deflat — CFF Recovery

**What:** Symbolic execution-based control flow flattening recovery for Binary Ninja. Identifies the dispatcher, traces state transitions, and rebuilds the original control flow graph.

**Source:** [github.com/cq674350529/deflat](https://github.com/cq674350529/deflat)

---

## Unpacking & Anti-Debug

### ScyllaHide — Anti-Debug Bypass

**What:** Advanced anti-anti-debug plugin for x64dbg, IDA, and OllyDbg. Hooks all known anti-debug APIs and PEB fields to hide the debugger from the target process.

**Bypasses:**
- `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`
- `NtQueryInformationProcess` (ProcessDebugPort, ProcessDebugFlags, ProcessDebugObjectHandle)
- `NtSetInformationThread` (ThreadHideFromDebugger)
- PEB flags: `BeingDebugged`, `NtGlobalFlag`, heap flags
- `NtQuerySystemInformation` (SystemKernelDebuggerInformation)
- Hardware breakpoint detection via `GetThreadContext`
- `OutputDebugString` exception handling
- `int 2d` / `int 3` SEH-based checks
- Timing checks (partial — patches `GetTickCount`/`QueryPerformanceCounter`)

**Install:** x64dbg: download from releases, copy to `plugins/`. IDA: copy to IDA plugins.

**Source:** [github.com/x64dbg/ScyllaHide](https://github.com/x64dbg/ScyllaHide)

---

### Scylla — IAT Reconstruction & Dumping

**What:** Import reconstruction tool. After unpacking a protected binary in memory, Scylla scans for the original import address table, resolves all imports, and produces a clean PE with a valid IAT.

**Use for:** Fixing the import table after dumping a packed/protected binary. The packer redirects imports through stubs — Scylla resolves them back to the real DLL functions.

**Source:** [github.com/NtQuery/Scylla](https://github.com/NtQuery/Scylla)

---

### pe-sieve — Process Hollowing Detector

**What:** Scans a running process for in-memory modifications: hollowed sections, injected code, hooked imports, replaced modules. Dumps the modified regions for analysis.

**Use for:** Detecting what a protector has modified in memory compared to the on-disk PE. Identifies unpacked/decrypted code regions.

**Source:** [github.com/hasherezade/pe-sieve](https://github.com/hasherezade/pe-sieve)

---

## String Extraction

### FLOSS — Obfuscated String Solver

**What:** FireEye Labs Obfuscated String Solver. Extracts strings from binaries even when they're constructed on the stack, XOR-encrypted, or dynamically generated. Uses emulation to execute string-construction routines and capture the cleartext.

**Extracts:**
- Stack strings (character-by-character construction)
- XOR-encrypted strings
- Base64-encoded strings
- Dynamically generated strings (via emulation)

**Install:**
```bash
pip install floss
```

**Source:** [github.com/mandiant/flare-floss](https://github.com/mandiant/flare-floss)

---

## Tracing & Instrumentation

### Intel PIN — Dynamic Instrumentation

**What:** Binary instrumentation framework. Injects analysis code into a running process at the instruction level. Used by Triton for symbolic execution and by custom trace tools.

**Use for:** Building custom VM tracers — instrument the dispatcher to log handler index + operands at every VM cycle.

**Source:** [intel.com/pin](https://www.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html)

---

### Frida — Dynamic Instrumentation Toolkit

**What:** JavaScript-based dynamic instrumentation. Inject scripts into running processes to hook functions, trace calls, modify behavior. Works on Windows, Linux, macOS, iOS, Android.

**Use for:** Quick API hooking (hook `VirtualProtect` to log unpacking), VM handler tracing (hook the dispatcher), import resolution (hook `GetProcAddress`).

**Install:**
```bash
pip install frida-tools
```

**Source:** [frida.re](https://frida.re/)

---

### DynamoRIO — Dynamic Instrumentation

**What:** Runtime code manipulation framework. Intercepts instruction execution for analysis, profiling, and modification. More performant than PIN for heavy instrumentation.

**Source:** [dynamorio.org](https://dynamorio.org/)

---

## Recommended Workflow by Protector

| Protector | Tool Chain |
|-----------|-----------|
| **VMProtect** | DIE (identify) → ScyllaHide (anti-debug) → NoVmp (devirtualize) → IDA (analyze) |
| **Themida (FISH/TIGER)** | DIE → ScyllaHide → x64dbg trace → handler mapping → manual lift |
| **Themida (EAGLE/SHARK)** | DIE → ScyllaHide → Triton (symbolic trace) → manual analysis |
| **OLLVM CFF** | D-810 (IDA) or deflat (BN) → automatic recovery |
| **OLLVM MBA** | Triton (simplification) or SSPAM → algebraic reduction |
| **Generic packer** | x64dbg → VirtualProtect bp → Scylla dump + IAT fix |
| **API hashing** | HashDB (IDA) → resolve all hashes in one pass |
| **Stack strings** | FLOSS → automated extraction |
| **Custom VM** | x64dbg/HyperDbg trace → Triton/Miasm lift → manual handler mapping |

---

## Source: `knowledge/engine-cryengine.md`

# CryEngine Reverse Engineering Reference

Engine-specific RE notes for the CryEngine family and its derivatives (Lumberyard / Open 3D Engine, Dunia, Star Citizen's "StarEngine" fork). Read this before attaching to a CryEngine title — the global-environment anchor, entity system, and camera math differ enough from Unreal/Unity/Source that the generic dumper workflow does not apply. This fills the gap left by `signatures/unreal-engine/` and `signatures/source2-engine/`, which say nothing about Crytek's `gEnv`-centric architecture.

> **Read this before** doing memory analysis on any CryEngine title, and read `skill://authorized-security-research` before pointing any tool at a live multiplayer build (Hunt: Showdown and Star Citizen both ship kernel anti-cheat).

---

## Engine Overview

CryEngine is Crytek's in-house C++ engine. There is no public offset dumper equivalent to Dumper-7 — you anchor everything from one global and walk pointer chains by hand.

| Generation | Era | Representative titles |
|------------|-----|-----------------------|
| CryEngine 1 | 2004 | Far Cry (original) |
| CryEngine 2 | 2007 | Crysis |
| CryEngine 3 | 2009–2013 | Crysis 2/3, Ryse, MechWarrior Online |
| CryEngine V (5.x) | 2015–present | Hunt: Showdown, Kingdom Come: Deliverance, Crysis Remastered trilogy |

**Architecture summary:**

- **Custom renderer.** D3D11 / D3D12 / Vulkan backends behind `IRenderer`. The engine owns its own deferred renderer; there is no third-party rendering middleware to anchor on.
- **Entity-Component model.** The world is a set of `IEntity` objects managed by `IEntitySystem`. Entities are addressed by a numeric `EntityId` and carry components (`IEntityComponent` in CryEngine V; the older proxy model in CE3). Gameplay code lives in `CryAction` (the game framework) on top of `CrySystem`.
- **In-house scripting / visual scripting.** Older titles embed **Lua** (the `IScriptSystem` surface). CryEngine V adds **Schematyc** (component-graph scripting) and the legacy **Flowgraph** node editor. These leave recognizable artifacts: Lua VM strings, Schematyc GUID tables, and Flowgraph node-name strings are excellent xref anchors.
- **Module split.** Functionality is spread across DLLs: `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, `CryRenderD3D11.dll`/`D3D12`, plus a per-game game DLL. Identify the module that owns the global before scanning it.

**Notable quirks:**

- The whole engine hangs off one global environment struct, `SSystemGlobalEnvironment`, reached through the `gEnv` pointer. Find `gEnv` and you reach the entity system, renderer, 3D engine, timer, and console from a single root.
- World space is **right-handed, Z-up** (Z is vertical). This is the opposite vertical axis from Y-up engines — bone/position math that assumes Y-up will be wrong here.
- Transforms are stored as CryEngine `Matrix34` (a 3×4 affine matrix, row-major in memory) and `Matrix44`. The camera exposes a `CCamera` with view and projection matrices; world-to-screen goes through these rather than a single packed view-projection global as on Source.

---

## Games Using This Engine

Grounded in commonly-known facts; treat anti-cheat and SDK columns as "what is publicly associated with the title," not a guarantee for the build in front of you.

| Game | Engine version | Notes | Anti-Cheat | Community SDK / dumper |
|------|----------------|-------|-----------|------------------------|
| Hunt: Showdown 1896 | CryEngine V | PvP extraction shooter; `gEnv`-rooted entity walk | EAC (EOS) | Forum-distributed offset tables; no public dumper |
| Star Citizen | Heavily forked CryEngine → Lumberyard ("StarEngine") | Diverged far from stock CryEngine; bespoke zone/entity system | EAC | Community ReClass dumps |
| Kingdom Come: Deliverance / KCD2 | CryEngine V | Single-player RPG; loose anti-tamper | None (SP) | CryEngine SDK as structural reference |
| Crysis Remastered (1/2/3) | CryEngine V (re-engineered) | Single-player | None (SP) | Original CryEngine 2/3 SDK headers |
| Ryse: Son of Rome | CryEngine 3 | Single-player | None (SP) | — |
| MechWarrior Online | CryEngine 3 | Online; per-build pattern scans | Server-side | — |

> Star Citizen's fork has drifted so far from stock CryEngine that generic CryEngine struct knowledge is only a starting hypothesis — confirm every offset against the live build.

---

## Memory Layout Patterns

Typical shapes to expect. **All struct offsets vary per build** — these describe the *kind* of layout, never a number to hardcode.

- **`gEnv` (the master anchor).** A pointer to `SSystemGlobalEnvironment` living in a data section of `CrySystem.dll` (sometimes the game DLL). The struct is a flat table of subsystem pointers:

```cpp
// SSystemGlobalEnvironment — field order varies by version, treat as illustrative
struct SSystemGlobalEnvironment {
    void*            pNetwork;
    IRenderer*       pRenderer;        // renderer + camera access
    void*            pPhysicalWorld;
    IEntitySystem*   pEntitySystem;    // entity enumeration root
    void*            pTimer;
    IScriptSystem*   pScriptSystem;    // Lua VM (older titles)
    I3DEngine*       p3DEngine;
    void*            pGameFramework;   // CryAction
    // ... many more subsystem pointers
};
```

- **Entity system.** `IEntitySystem` owns the live entity set. Internally it keeps an array/map of `CEntity*` indexed by `EntityId`. The iteration entry point is an `IEntityIt` (entity iterator) or a direct array base — both are reachable from the `pEntitySystem` pointer. Each `CEntity` carries its name, flags, world transform (`Matrix34`), and component list.

- **Entity world position.** Stored on the entity's transform as a `Vec3` of `float32` (`read_vec3_fl32`), Z-up. Larger maps may keep a world-segment offset; confirm whether positions are absolute or segment-relative.

- **Local player / camera.** Reached through the game framework (`CryAction`) actor system: `IActorSystem → local actor → entity`. The renderable camera is a `CCamera` exposed by the renderer/view system; it holds the view matrix, projection matrix, position, and FOV used for projection.

- **View / projection matrices.** CryEngine uses `Matrix44` for projection and a `Matrix34` view, row-major. There is generally **no single packed 4×4 view-projection global** to scan for as on Source — build the VP yourself from the camera matrices, or locate the per-frame composed matrix the renderer caches.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md` and `signatures/unreal-engine/ue-reversal-guide.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`. Re-derive every byte against your target; verify exactly one hit.

```
gEnv pointer
Description: MOV reg, [rip+????] loading the global environment pointer,
             referenced everywhere the engine touches a subsystem.
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 8B 88        (MOV RAX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → SSystemGlobalEnvironment*
Anchor tip:  xref a CrySystem console-variable string ("sys_") or an engine
             init string; the init path stores gEnv.
```

```
Entity system access
Description: LEA/MOV that loads gEnv->pEntitySystem before an entity call.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01 FF 50  (MOV RCX, [rip+????]; call vtable)
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7); often easier to read the
             field offset off gEnv than to scan separately.
```

```
Lua VM / script system (older CE titles)
Description: reference to the global lua_State the engine spins up.
Anchor tip:  xref Lua error strings ("attempt to index", "PANIC") or registered
             function-name strings to reach the script system pointer.
```

**Anchor-string strategy (most reliable on CryEngine):** the engine ships thousands of stable strings — CVar names (`"sv_"`, `"sys_"`, `"r_"`, `"e_"`), Flowgraph node names, Schematyc type names, and `.cry`/`.pak` asset paths. Xref a stable string → reach the function that uses the global → copy the load instruction. This beats blind opcode scanning because the recompiled game DLL moves code but keeps the strings.

---

### Verifying and Maintaining Sigs

Every sig must produce exactly one hit in its owning module, or the resolved address is meaningless. Scan, count, and extend:

```cpp
// Confirm a sig is unique before trusting its RIP resolution.
array<uint64> hits = p.find_all_code_patterns(g_base, g_size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
    // > 1: extend the sig with more surrounding bytes until unique.
    // 0  : the function was recompiled — re-derive from a fresh string xref.
}
```

On CryEngine the cheapest re-derivation path after a patch is the **string-xref anchor**, not blind opcode search: the CVar / Flowgraph / Schematyc strings survive recompiles even when the surrounding code bytes move, so they regenerate the `gEnv` and subsystem sigs reliably. Keep the anchor string recorded alongside each sig so the offset-maintainer can rebuild it.

## Reversal Workflow

Recommended first 60 minutes on an unknown CryEngine build:

1. **Identify the module that owns `gEnv`.** Enumerate modules (`p.get_module_list()`): `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, and the per-game DLL confirm CryEngine. Star Citizen ships its fork under different module names — confirm via the renderer DLL and string content.
2. **Find `gEnv` first — everything else hangs off it.** Use the CVar/init-string xref anchor. Resolve it, dereference, and sanity-check that the subsequent pointers land in valid module/heap ranges (`p.is_valid_address`).
3. **Walk to `pEntitySystem`** off `gEnv`, then dump the entity iterator/array. Read a handful of entities' name strings to confirm you have the right field — entity names are the cheapest correctness check on this engine.
4. **Walk to the local actor** through `pGameFramework` (CryAction) → actor system → local actor → entity, and to the **camera** through the renderer/view. Confirm Z-up by reading your own position and moving in-game.
5. **Tooling.** IDA + Ghidra both decompile CryEngine cleanly (it is straightforward C++ with RTTI). Use `analyze_vtable` / `read_rtti` on `IEntitySystem` and `CCamera` — Crytek leaves RTTI in many builds, which names the classes for you. Schematyc/Flowgraph strings give you a second, independent anchor when a CVar sig is ambiguous.
6. **Confirm before hardcoding.** Pattern-scan `gEnv`; resolve subsystem pointers as field reads off it (not separate scans); treat struct field offsets as per-build and re-verify each patch.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md` for AC internals. Guidance level only.

- **Hunt: Showdown 1896 → EAC (EOS).** Full kernel anti-cheat: handle stripping, module/integrity scans, hypervisor checks. Treat exactly as the EAC profile in `anti-cheat-architecture.md`. The single-`gEnv` anchor does nothing to reduce AC exposure — reading still happens against a protected process.
- **Star Citizen → EAC.** Same EAC kernel surface; the engine fork does not change the AC model.
- **Single-player titles (Kingdom Come, Crysis Remastered, Ryse) → no anti-cheat.** Anti-tamper is loose to absent, which is why CryEngine SDK headers and reversed offsets circulate freely for these — but that freedom is specific to the SP titles, not the engine.
- **Engine-specific detection surface:** the Lua/Schematyc scripting layer is an in-process attack surface; titles that expose modding lock it down, and AC builds watch for foreign script registration. Do not assume the scripting hooks that work on KCD work on Hunt.

---

## Community Tools and Resources

Refer to categories by name and search for the current source yourself — no live cheat-distribution links here.

- **CryEngine SDK / CryEngine V launcher source** — the official engine source and headers are the authoritative structural reference for stock CryEngine. Single best resource for class layouts (`IEntity`, `IEntitySystem`, `CCamera`, `SSystemGlobalEnvironment`).
- **CryEngine 2 / 3 leaked or licensee SDK headers** — structural reference for older Crysis-era titles.
- **Star Citizen community reversing groups** — ReClass dumps and forum offset threads for the StarEngine fork.
- **Forum offset tables** ("CryEngine offsets" threads on the usual RE/game-hacking forums) — per-build entity-list and camera offsets; always stale after a patch.
- **RTTI/vtable dumpers** (generic) — because Crytek ships RTTI, a vtable/RTTI dumper recovers class names directly from the binary.

---

## Coordinate System and World-to-Screen

CryEngine world space is **right-handed, Z-up**: X/Y are the ground plane, Z is vertical. Any math copied from a Y-up engine (most Unity/UE bone code) has the vertical axis wrong and must be remapped.

There is generally no single packed view-projection global to scan for. Build the projection from the `CCamera`'s view and projection matrices (or locate the per-frame composed matrix the renderer caches), then project. The matrix-major order must be confirmed by reading it out and projecting a known point — do not assume Source's row-major layout.

```cpp
// Sketch — project a world point through a cached VP matrix (Enma-style).
// OFF_* are resolved via sig/struct_dump per build, never hardcoded here.
// Follows the W2S discipline: read once, w > 0.001 guard, vecs built per frame.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    // Read the matrix once; verify row vs column major against your build first.
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z   // Z is vertical on CryEngine
              + p.rf32(vp_addr + 60);
    if (w < 0.001) return false;                 // behind camera (guideline 10)
    float64 inv_w = 1.0 / w;
    float64 nx = (p.rf32(vp_addr + 0) * world.x + p.rf32(vp_addr + 16) * world.y
               +  p.rf32(vp_addr + 32) * world.z + p.rf32(vp_addr + 48)) * inv_w;
    float64 ny = (p.rf32(vp_addr + 4) * world.x + p.rf32(vp_addr + 20) * world.y
               +  p.rf32(vp_addr + 36) * world.z + p.rf32(vp_addr + 52)) * inv_w;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

> UNVERIFIED for any specific build — confirm the matrix layout and column/row offsets against your target before trusting projected coordinates.

## Offset Stability Reference

Where the key values typically live and how stable each is. "Stability" is about the *resolution method*, not a number — the address changes every build; a good sig does not.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| `gEnv` | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; one pointer to all subsystems |
| `gEnv->pEntitySystem` | Field read off `gEnv` | High | Entity enumeration root |
| `gEnv->pRenderer` | Field read off `gEnv` | High | Camera / `CCamera` access |
| `gEnv->p3DEngine` | Field read off `gEnv` | High | World / scene queries |
| `gEnv->pGameFramework` | Field read off `gEnv` | High | CryAction; actor system → local actor |
| `gEnv->pScriptSystem` | Field read off `gEnv` | High | Lua VM (older titles) |
| Entity array / iterator | Off `pEntitySystem` | Medium | Layout varies; confirm via entity-name read |
| `CEntity` world transform | Per-entity offset | Medium | `Matrix34`, Z-up; position is `Vec3` float32 |
| Local actor / pawn | Actor system → local actor → entity | Medium | Game-specific gameplay fields |
| `CCamera` view / projection | Renderer / view system | Medium | Build VP from these; verify major order |

**Rules of thumb:**
- `gEnv` is a pointer in the module image → pattern-scan + RIP-resolve, never hardcode the address.
- Prefer **field reads off `gEnv`** over separate scans for each subsystem — one stable anchor beats five fragile ones.
- Everything below `CEntity` is game-specific; re-derive per build with `struct_dump` and an entity-name correctness check.

## Engine / Build Identification

Confirm you are on CryEngine (and which fork) before applying any of the above:

- **Module list** (`p.get_module_list()`): `CrySystem.dll`, `CryEntitySystem.dll`, `CryAction.dll`, `Cry3DEngine.dll`, `CryRenderD3D11.dll`/`D3D12`, plus a per-game DLL.
- **String markers:** CVar prefixes (`sys_`, `r_`, `e_`, `sv_`), Flowgraph node names, Schematyc type names, `.pak`/`.cry` asset paths.
- **Fork detection:** Star Citizen's StarEngine renames/repackages modules and diverges heavily — confirm via renderer DLL and string content, and treat stock CryEngine struct knowledge as a hypothesis only.
- **Version:** the engine version string (often near init/log strings) tells you CE3 vs CE V; the entity-component model (CE V) vs entity-proxy model (CE3) changes the component-walk shape.

## Common Pitfalls

- **Assuming Y-up.** CryEngine is Z-up. Bone/position math ported from a Y-up engine swaps the wrong axis and puts ESP boxes on their side — the most common first-attempt failure here.
- **Scanning each subsystem separately.** Five fragile sigs (one per subsystem) break independently every patch. Resolve `gEnv` once and read subsystems as field offsets — one anchor to maintain.
- **Hardcoding the entity-array layout.** The entity container shape varies (array vs iterator) across CE3 and CE V. Always confirm with an entity-name read before trusting the iteration.
- **Trusting RTTI on stripped builds.** Crytek leaves RTTI in many builds but not all; when `read_rtti` returns nothing, fall back to string-xref anchors rather than assuming the class is gone.
- **Star Citizen ≠ stock CryEngine.** The StarEngine fork diverges enough that stock struct knowledge is a hypothesis, not a map. Re-derive everything.
- **Forgetting the renderer caches no single VP global.** Build the view-projection from `CCamera`, or find the per-frame composed matrix; do not waste time scanning for a Source-style packed VP that is not there.
- **Reading positions as segment-relative when they are absolute (or vice versa).** Large maps may offset positions by a world segment; verify by comparing a read against your in-game coordinates.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — EAC architecture and detection vectors (Hunt, Star Citizen).
- `knowledge/game-targets.md` — Hunt: Showdown listed under Tactical/Team; engine column = CryEngine.
- `knowledge/offset-methodology.md` — RIP resolution, `struct_dump`, sig-vs-hardcode discipline.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, and GUI patterns to wire resolved offsets into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification (same technique).
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `analyze_vtable`/`read_rtti` for class recovery.
- `skill://anti-cheat-re` — six-step AC methodology for the EAC-protected titles.
- `skill://authorized-security-research` — scope/authorization before touching a live protected build.
- If you derive stable patterns, drop a stub under `signatures/cryengine/` mirroring the `signatures/unreal-engine/` layout.

---

## Source: `knowledge/engine-frostbite.md`

# Frostbite Reverse Engineering Reference

Engine-specific RE notes for DICE/EA's Frostbite engine (Battlefield, Battlefront, FIFA / EA Sports FC, Dragon Age, Mass Effect Andromeda, Anthem, Need for Speed, Madden). Read this before attaching to a Frostbite title — its data-driven entity bus, manager-chain layout, and `RenderView` camera model are unlike Unreal/Unity/Source, and there is no managed runtime to dump from. This fills the gap left by the existing UE/Unity/Source signature guides.

> **Read this before** doing memory analysis on any Frostbite title, and read `skill://authorized-security-research` first — modern Battlefield and FC titles ship EA AntiCheat (EAAC), a kernel-mode anti-cheat.

---

## Engine Overview

Frostbite is a closed, in-house C++ engine. There is no public SDK and no dumper; the community reverses it by hand, and the canonical entity/manager chain has been stable enough across titles that the *shape* (not the offsets) is well understood.

| Generation | Era | Representative titles |
|------------|-----|-----------------------|
| Frostbite 1 | 2008 | Battlefield: Bad Company |
| Frostbite 2 | 2011 | Battlefield 3 / 4, Need for Speed |
| Frostbite 3 (later just "Frostbite") | 2013–present | Battlefield 1 / V / 2042, Battlefront I / II, Dragon Age: Inquisition / Veilguard, Mass Effect Andromeda, Anthem, FIFA / EA Sports FC, Madden, Plants vs. Zombies |

**Architecture summary:**

- **Custom deferred renderer.** D3D11 / D3D12 backends. The render path exposes a `GameRenderer` → `RenderView`, where `RenderView` carries the view/projection transform used for projection.
- **Data-driven Entity Bus ("EBX").** Frostbite is built around a typed, data-driven asset/object model. Runtime objects derive from a reflected type system; gameplay is assembled from EBX asset data rather than hand-written per-actor C++. There is **no exposed managed scripting layer** (no Mono/IL2CPP, no Lua surface to enumerate) — this is pure native C++ with a custom reflection system, so you reverse it like any C++ binary.
- **Manager-chain object model.** The community-stable access pattern is a chain of singleton managers: `ClientGameContext` → `ClientPlayerManager` → player array → `ClientPlayer` → `ClientSoldierEntity` (the controllable body) → component pointers (health, transform, weapon). Spectator/local input flows through a `BorderInputNode`-style local-player node.
- **DICE C++ with symbols-friendly structure.** Frostbite binaries are large, optimized C++ but FLIRT/IDA signatures and RTTI-style class identification work well — this is one of the more tractable proprietary engines to reverse statically.

**Notable quirks:**

- The local player and the entity list are reached through **different chains** off `ClientGameContext` — one via `ClientPlayerManager`, one via the player array. Don't assume a single root array like Source.
- World-space convention is title-dependent. Frostbite has historically used a **Y-up** world with the renderer composing a view-projection in `RenderView`; whether the cached matrix is row- or column-major has varied across titles — **read it out and verify empirically** before committing W2S math. Do not assume the Source row-major layout.

---

## Games Using This Engine

Grounded in commonly-known facts. Treat the anti-cheat column as "publicly associated with the title," and note EA migrated titles from PunkBuster → FairFight → EA AntiCheat over time.

| Game | Engine | Notes | Anti-Cheat | Community SDK / dumper |
|------|--------|-------|-----------|------------------------|
| Battlefield 2042 | Frostbite | Manager-chain entity walk | EA AntiCheat (EAAC, kernel) | Forum ReClass dumps |
| Battlefield V / 1 | Frostbite | Per-build pattern scans | EAAC (later builds); FairFight (server) | Forum offset tables |
| Battlefield 4 / 3 | Frostbite 2/3 | Most-documented community target | PunkBuster (PB) + FairFight historically | Extensive forum class dumps |
| Star Wars Battlefront II | Frostbite | Similar soldier-entity layout | EAAC / FairFight | — |
| EA Sports FC / FIFA | Frostbite | Sports title; different gameplay objects | EAAC | — |
| Dragon Age: Inquisition / Veilguard | Frostbite | Single-player RPG | None / DRM only (SP) | — |
| Mass Effect: Andromeda | Frostbite | Single-player | None (SP) | — |
| Anthem | Frostbite | Online looter-shooter | EAAC / server-side | — |
| Need for Speed (Frostbite era) | Frostbite | Racing | EAAC (online) | — |

> AC association is era-dependent: a title shipped under PunkBuster years ago may now enforce EAAC. Confirm the loaded AC driver/service at runtime rather than trusting this table for a current build.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — these describe the layout *kind*, never a number to hardcode.

- **`ClientGameContext` (the manager root).** A global singleton pointer in the game module's data section. From it you reach the player manager, the entity/game-world references, and the level state:

```cpp
// Illustrative — community-stable shape, field offsets per build
struct ClientGameContext {
    ClientPlayerManager* playerManager;   // local + remote players
    void*                gameWorld;        // world / level state
    void*                levelManager;
    // ... additional manager pointers
};
```

- **Player enumeration.** `ClientPlayerManager` holds the local player pointer and an array of `ClientPlayer*` (remote players). Each `ClientPlayer` references its controlled `ClientSoldierEntity`:

```cpp
struct ClientPlayerManager {
    ClientPlayer*  localPlayer;
    ClientPlayer** players;       // array of remote players
    int32          maxPlayers;    // iteration bound
};

struct ClientPlayer {
    ClientSoldierEntity* controlledControllable;  // the soldier body, null when dead/spectating
    int32                teamId;
    // name, ping, score elsewhere in the struct
};
```

- **`ClientSoldierEntity` (the body).** Carries the component pointers cheats read: a health component, a soldier-prediction/transform source for world position (`Vec3`/`Vec4` of `float32`, Y-up), and the weapon/aim components. Position is frequently read off the prediction component or the entity transform — confirm which is authoritative per build.

- **Camera / `RenderView`.** Reached through `GameRenderer` → `RenderView`. `RenderView` holds the view transform, projection, FOV, and camera position. World-to-screen multiplies world position through the `RenderView` matrix — **verify matrix-major order by reading the matrix and projecting a known point**, do not copy Source's layout blindly.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit.

```
ClientGameContext singleton
Description: MOV reg, [rip+????] loading the game-context singleton pointer,
             referenced anywhere gameplay touches the player manager.
Sig shape:   48 8B 05 ?? ?? ?? ?? 48 8B 88        (MOV RAX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → ClientGameContext*
Anchor tip:  xref a Frostbite gameplay/CVar string or a render-pass name string;
             EBX type-name strings also anchor reliably.
```

```
GameRenderer / RenderView
Description: LEA/MOV loading the renderer singleton before composing RenderView.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B   (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → GameRenderer*
Anchor tip:  xref render-pass / pipeline name strings; the renderer init stores it.
```

**Anchor-string strategy (most reliable on Frostbite):** Frostbite ships stable EBX type names, render-pass names, and gameplay strings. Xref a stable string → reach the function using the manager → copy the load instruction. Because DICE C++ keeps RTTI-style structure, `analyze_vtable` / `read_rtti` on the manager and renderer classes often names them outright, which is a stronger anchor than opcode scanning.

---

```
ClientPlayerManager / local player
Description: access to the player manager and the local-player slot, reached
             off ClientGameContext or via its own load instruction.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 81 ?? ?? ?? ?? 48 85 C0  (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7); prefer reading the
             manager as a field off ClientGameContext once that is anchored.
Anchor tip:  xref a player/spawn gameplay string near the manager init.
```

### Verifying and Maintaining Sigs

Every sig must produce exactly one hit in its owning module, or the resolved address is meaningless. Scan, count, and extend:

```cpp
// Confirm a sig is unique before trusting its RIP resolution.
array<uint64> hits = p.find_all_code_patterns(g_base, g_size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
    // > 1: extend the sig with more surrounding bytes until unique.
    // 0  : the function was recompiled — re-derive from a fresh string xref.
}
```

Frostbite's large optimized binary tends to repeat short opcode sequences, so raw byte patterns often start non-unique — expect to extend them with several surrounding bytes. The **EBX type-name / render-pass string anchors** are the durable re-derivation path after a patch; because Frostbite keeps RTTI-style structure, `read_rtti` on the manager and renderer classes is often a faster relocate than re-scanning. Record the anchor string and class name with each sig.

## Reversal Workflow

Recommended first 60 minutes on an unknown Frostbite build:

1. **Confirm it is Frostbite.** Module list shows a single large game executable plus Frostbite-characteristic DLLs; render-pass and EBX type strings in the binary confirm it. No `GameAssembly.dll` / `mono*.dll` (not Unity), no `*-Win64-Shipping.exe` UE marker.
2. **Find `ClientGameContext` first.** It is the root of the manager chain — resolve it via the gameplay/EBX string xref anchor, dereference, and sanity-check that `playerManager` lands in a valid range.
3. **Walk to the local player and player array** via `ClientPlayerManager`. Read team IDs and player names early — they are the cheapest correctness check that you have the right offsets.
4. **Walk to `ClientSoldierEntity`** via `controlledControllable`; null it out gracefully (it is null when dead/spectating). Read your own position and health to confirm the transform/health components.
5. **Find `GameRenderer` → `RenderView`** and read the view matrix. **Project a known world point and verify on screen** before trusting matrix-major order or axis convention.
6. **Tooling.** IDA + FLIRT signatures and Ghidra both excel here — Frostbite is large but clean DICE C++. Use `analyze_vtable`/`read_rtti` to name manager and renderer classes. Confirm before hardcoding; treat every offset as patch-volatile.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Modern Battlefield / Battlefront / FC / Anthem → EA AntiCheat (EAAC).** EA's in-house kernel-mode anti-cheat (`EAAntiCheat.GameService` service + kernel driver). Treat it as a full kernel AC: handle stripping, module/integrity scans, and the usual ring-0 callback surface described for EAC/BattlEye in `anti-cheat-architecture.md`. It loads with the protected title.
- **Legacy / server-side layers.** Older Battlefield titles shipped **PunkBuster (PB)** (user-mode, screenshot + scan) and EA's server-side **FairFight (FF)** statistical/behavioral detection. FairFight runs server-side and is independent of how you read memory. Many titles now run EAAC *plus* FairFight.
- **Single-player titles (Dragon Age, Mass Effect Andromeda) → no anti-cheat,** DRM only. The manager-chain knowledge that circulates for these is SP-specific; do not assume it transfers to a protected multiplayer build untouched.
- **Engine-specific note:** Frostbite ships EAAC integration in the online titles, so the foreign-module and handle-access detection applies the moment you attach. The lack of a managed runtime means there is no script-layer detection surface (unlike RE Engine / Unity), but also no managed metadata to lean on — everything is native.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **Battlefield reversing threads** (the usual game-hacking / RE forums) — the most-documented community target is the BF3/BF4 era, where `ClientGameContext`/`ClientPlayerManager`/`ClientSoldierEntity`/`RenderView` class layouts were dumped and re-dumped. Use those as the structural template; offsets are stale.
- **ReClass.NET project files** for Frostbite titles — community-maintained struct definitions you import into ReClass to navigate live memory.
- **Forum offset tables** — per-build entity-array, local-player, and `RenderView` offsets; always re-verify after a patch.
- **IDA / Ghidra + RTTI dumpers** — because Frostbite is clean C++ with RTTI structure, generic vtable/RTTI tooling recovers class names directly.

---

## Coordinate System and World-to-Screen

Frostbite's world convention is title-dependent and historically **Y-up**, with the renderer composing a view-projection into `RenderView`. Crucially, whether the cached matrix is row- or column-major **has varied across Frostbite titles** — this is the single most common source of broken W2S on this engine. Read the matrix out and project a known point before committing.

```cpp
// Sketch — project through the RenderView view-projection matrix (Enma-style).
// OFF_* resolved via sig/struct_dump per build. Verify matrix-major order FIRST.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z
              + p.rf32(vp_addr + 60);
    if (w < 0.001) return false;                 // behind camera (guideline 10)
    float64 inv_w = 1.0 / w;
    float64 nx = (p.rf32(vp_addr + 0) * world.x + p.rf32(vp_addr + 16) * world.y
               +  p.rf32(vp_addr + 32) * world.z + p.rf32(vp_addr + 48)) * inv_w;
    float64 ny = (p.rf32(vp_addr + 4) * world.x + p.rf32(vp_addr + 20) * world.y
               +  p.rf32(vp_addr + 36) * world.z + p.rf32(vp_addr + 52)) * inv_w;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

> UNVERIFIED for any specific build. If projected points mirror or invert, your matrix-major assumption is wrong — transpose the index mapping and re-test before touching anything else.

## Offset Stability Reference

Where the key values typically live and how stable each is. "Stability" describes the resolution method, not a number.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| `ClientGameContext` | Module data section, sig + RIP | None (address) / High (sig) | Manager-chain root |
| `ClientPlayerManager` | Field off `ClientGameContext` | Medium | Local player + remote array |
| Local player | Field off `ClientPlayerManager` | Medium | Distinct from the remote array |
| Remote player array + count | Off `ClientPlayerManager` | Medium | Iterate to `maxPlayers` |
| `ClientPlayer::controlledControllable` | Per-player offset | Medium | Null when dead/spectating |
| `ClientSoldierEntity` position | Transform / prediction component | Medium | `Vec3`/`Vec4` float32, Y-up |
| `ClientSoldierEntity` health | Health component | Medium | Confirm authoritative source |
| `GameRenderer` | Module data section, sig + RIP | None / High | Renderer singleton |
| `RenderView` view-projection | Off `GameRenderer` | Medium | Verify major order before W2S |

**Rules of thumb:**
- The two singletons (`ClientGameContext`, `GameRenderer`) are pointers in the image → sig + RIP, never hardcode.
- Local player and entity list are **separate chains** off the context — resolve both, do not assume one array.
- All `Client*Entity` gameplay fields are per-build → `struct_dump` + a team-ID/name correctness check; re-derive each patch.

## Engine / Build Identification

Confirm you are on Frostbite before applying any of the above:

- **Module list** (`p.get_module_list()`): a single large game executable; **no** `GameAssembly.dll`/`mono*.dll` (rules out Unity) and **no** `*-Win64-Shipping.exe` (rules out UE).
- **String markers:** EBX type names, render-pass / pipeline names, and DICE gameplay strings in the binary.
- **AC markers:** an `EAAntiCheat.GameService` service / EAAC driver indicates a current protected build regardless of the title's launch-era anti-cheat.
- **Era matters for layout:** BF3/BF4-era class layouts are the most-documented community template, but field offsets and even the chain shape drift across Frostbite generations — use the era closest to your target as the starting hypothesis only.

## Common Pitfalls

- **Wrong matrix-major order in `RenderView`.** The single most common Frostbite W2S failure: the cached view-projection has varied between row- and column-major across titles. If points mirror or invert, transpose the index mapping before changing anything else.
- **Treating local player and entity list as one root.** They live on separate chains off `ClientGameContext` (player manager vs player array). Resolve both.
- **Not null-checking `controlledControllable`.** It is null whenever the player is dead or spectating; dereferencing it unguarded crashes the loop on the first downed player.
- **Porting BF3/BF4 offsets directly.** Those are the best-documented layouts but field offsets drift across Frostbite generations; use them as a starting hypothesis, then `struct_dump` and verify.
- **Reading position from the wrong component.** Position may live on a prediction component or the entity transform; pick the authoritative one for the build, or your ESP lags or jitters.
- **Assuming no EAAC because an old guide says PunkBuster.** AC is era-dependent; a title patched onto EAAC is a kernel-AC target now regardless of what shipped at launch. Check the loaded driver/service.
- **Looking for a managed runtime.** There is none — no Mono/IL2CPP, no Lua surface to enumerate. Everything is native C++; reverse it as such.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — EAC/BattlEye kernel model; apply the same lens to EAAC.
- `knowledge/game-targets.md` — engine-by-game table for cross-checking AC associations.
- `knowledge/offset-methodology.md` — RIP resolution, `struct_dump`, sig-vs-hardcode discipline.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved offsets into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `analyze_vtable`/`read_rtti`.
- `skill://anti-cheat-re` — six-step AC methodology for EAAC-protected titles.
- `skill://authorized-security-research` — scope/authorization before touching a live protected build.
- If you derive stable patterns, add a stub under `signatures/frostbite/` mirroring `signatures/unreal-engine/`.

---

## Source: `knowledge/engine-godot.md`

# Godot Reverse Engineering Reference

Engine-specific notes for Godot Engine titles (Godot 3.x C++ core, Godot 4.x rewritten core with Vulkan and dual GDScript/C# support). Read this before attaching to a Godot title — the node-tree architecture, the `ObjectDB` indirection, and the embedded-script `.pck` payload differ enough from Unreal/Unity/Source that the generic dumper workflow does not apply. This fills the gap left by the other engine references (CryEngine, Frostbite, RE Engine, REDengine, Source, Unreal, Unity).

> **Read this before** doing memory analysis on any Godot title. Godot is open-source — pull the matching engine version from `github.com/godotengine/godot` and grep the actual headers; this is a fundamental RE advantage no closed-source engine offers.

> **Scope:** Educational reference. See `skill://authorized-security-research` before pointing any offensive tool at a live multiplayer build.

---

## Engine Overview

Godot ships as a single self-contained executable that embeds the GDScript bytecode, scenes, and resources inside a PCK archive appended to (or alongside) the engine binary. The user runs `MyGame.exe`; the engine code, the game's compiled scripts, and the assets all live in or beside that one file.

Two distinct lineages:

- **Godot 3.x** — C++ core, GLES2/GLES3 renderer, GDScript 1.0. Long-tail of shipped titles. Smaller binary, simpler RE target.
- **Godot 4.x** — rewritten core, Vulkan/D3D12/Metal renderers, GDScript 2.0 (typed, partially compiled), first-class C# (Mono) support. Larger binary, more API surface, the current default for new projects.

Both share architectural primitives:

- **Node tree** — every game-world object is a `Node`; the running game is a `SceneTree` whose root node has the current scene attached. Almost every gameplay query starts at `SceneTree::get_root()` and walks children.
- **Object / RefCounted / Resource** — three lifetime models. `Object` is manually managed; `RefCounted` (Godot 4) / `Reference` (Godot 3) is refcounted; `Resource` is refcounted + serializable. Knowing which one a class inherits from tells you how to keep a pointer alive across frames.
- **ObjectDB** — every `Object` registers in a global hash table keyed by a 64-bit `ObjectID`. To find any object from outside the engine, you walk this table. `ObjectDB::instances` is the global symbol.
- **RID system** — the rendering server, physics server, and audio server allocate opaque `RID` handles (64-bit integers) for GPU resources, physics bodies, etc. The mapping from `RID` → underlying allocation is per-server.
- **Singletons** — `Engine`, `OS`, `SceneTree`, `RenderingServer`, `PhysicsServer3D`, `Input`, `ResourceLoader`. Each is accessible via `get_singleton()` and is the entry point to its subsystem.

---

## Games Using This Engine

| Game | Godot Version | Notes | Anti-Cheat |
|---|---|---|---|
| Brotato | 4.x | Bullet-heaven roguelite; widely studied for mods | None (single-player) |
| Cassette Beasts | 4.x | Open-world monster-collector | None (single-player) |
| Halls of Torment | 4.x | Diablo-meets-Vampire-Survivors | None (single-player) |
| Endoparasitic | 4.x | Single-player horror; small surface | None |
| Buckshot Roulette | 4.x | Single-player; later online expansion via separate mod | None on the base game |
| Slay the Princess | 4.x | Visual-novel hybrid | None |
| Dome Keeper | 3.x | Tower-defense hybrid | None (mostly single-player) |
| The Case of the Golden Idol | 3.x | Detective puzzle | None |
| Cruelty Squad | 3.x | First-person shooter | None |
| Cassette Beasts: Pier of the Unknown | 4.x | DLC | None |

The export-template trick: when Godot builds a release, it appends the project's compiled `.pck` (containing every script, scene, image, sound) to the end of the engine executable. The footer carries a magic header `GDPC`, a version byte, and an index. Any change to scripts changes the binary hash — a soft tamper-detect that some titles cross-reference against an online manifest.

Multiplayer Godot titles are rare and almost always lean on authoritative server logic or third-party validation; client-side enforcement is the exception.

---

## Memory Layout Patterns

The patterns to find first when attaching to a Godot binary:

- **`OS::get_singleton()`** — the OS singleton is the gateway to almost everything. Its static slot is referenced by literally every singleton accessor; find the slot, you've found a Rosetta Stone.
- **`SceneTree` root** — accessible via `OS::get_singleton()->get_main_loop()` (returns a `MainLoop*` which is the `SceneTree*` in a running game). From the root, walk children to find the active scene, then game-specific nodes by their assigned name strings (`Player`, `Enemy`, etc.).
- **`ObjectDB::instances` hash table** — a flat hash map of `ObjectID` → `Object*`. The table size is power-of-two; entries are tombstone-deletable. To enumerate every live object: walk the table, skip tombstones, deref the `Object*`. Then read `Object::_class_name` (a string ID) to figure out what each one is.
- **`ClassDB` registered classes** — the class-registration table is built at startup and never grows after engine init. A pointer scan for the string `"Object"` lands you in or near the `ClassDB` entry table; from there, walk to find every registered class name, its parent, its method table.
- **Active camera** — `RenderingServer` holds the active camera RID; resolve via `RenderingServer::camera_get_*` accessors. The camera's transform is a `Transform3D` (a 4x3 affine: 3x3 basis + 3-component origin), NOT a 4x4 view matrix — derive the view matrix yourself or use the inverse of the camera transform.
- **GDScript bytecode** — instances of `GDScript` (a `Resource`) carry their compiled bytecode in a flat `Vector<uint8_t>`. The instruction format is in `core/object/script_language.h` + `modules/gdscript/gdscript.h` upstream. For reversal of game logic, decompiling the bytecode (see Community Tools below) is faster than reading the running VM state.

Coordinate convention: Godot 4 uses **Y-up, right-handed** by default. Godot 3 also Y-up. Most games keep the default, but check the project settings (embedded in the PCK) before assuming.

---

## Common Sigs and RIP Patterns

Illustrative byte-pattern *shapes* to look for. Do not commit to specific byte sequences — they change between Godot versions and compiler builds. The shape is stable; the bytes are not.

- **Singleton accessor pattern** — `MOV rax, [rip+disp32]; TEST rax, rax; JNZ ...; CALL _init; MOV [rip+disp32], rax`. This is the lazy-init pattern for `OS::get_singleton()`, `Engine::get_singleton()`, etc. The first `MOV` reads the static slot; the slot address is what you want.
- **`ObjectDB::instances` access** — `LEA rcx, [rip+disp32]` where `rip+disp32` is the static instances-table address; followed by a hash-and-probe loop. Find the `ClassDB` init function for a reliable xref into this region.
- **`SceneTree::process` tick** — the main game loop calls `SceneTree::process(float delta)` every frame. This is one of the longer functions in the binary and contains string references to "process", "_process", "physics_process". String xref → function → top of frame.
- **GDScript VM dispatch** — a giant switch / computed-goto on opcode bytes. The dispatcher reads from the `GDScript`'s bytecode `Vector<uint8_t>`; the opcode table size matches `GDScriptFunction::Opcode` enum in the upstream source.

Always cross-reference candidate sigs against the open-source headers from the matching Godot release tag. If a sig matches no instruction the upstream source describes, you've either got the version wrong or the title has a modified engine fork.

---

## Reversal Workflow

The recommended first 60 minutes on a fresh Godot binary:

1. **Identify the version.** The engine writes a `"Godot Engine v<X.Y.Z>"` string at startup. ASCII string scan in `.rdata` finds it instantly. Note both major.minor (e.g. `4.2`) and the patch (e.g. `4.2.1.stable`).
2. **Pull the matching headers.** `git clone github.com/godotengine/godot && git checkout <X.Y.Z>-stable`. You now have the actual `Object`, `Node`, `SceneTree`, `RenderingServer`, `GDScriptFunction` definitions the binary was compiled from. This is the open-source RE advantage; use it before anything else.
3. **Locate `OS::get_singleton()`.** String xref on `"OS"` won't help (too many matches); instead, find a known accessor like `MainLoop *OS::get_main_loop()` by its symbol name in the GitHub source, find its call sites, and the slot it reads is `OS::singleton`.
4. **Enumerate `ClassDB`.** Once you have `OS`, the `ClassDB::class_list` member is reachable; walk it and dump the per-class name + parent + method table. This gives you a full class hierarchy as a starting map.
5. **Find `SceneTree::get_root()`.** From `OS::get_main_loop()`, follow to `SceneTree`; the `root` field is a `Window*` (Godot 4) or `Viewport*` (Godot 3). Walk children from there into game-specific scene structure.
6. **Locate the active camera.** Either via `RenderingServer::camera_get_current()` or by walking the scene tree looking for the `Camera3D` node. Once found, the view matrix (or its derivation) is yours.
7. **Identify gameplay nodes by string.** Most games name their player node literally `"Player"` and enemies `"Enemy"` or specific subclasses. Walk the scene tree, match by name, then read the relevant `_class_name` to know what struct to read against.

The `.pck` payload is its own RE target: use a `.pck` extractor (see Community Tools) to pull out every script, scene, and resource as readable files. For Godot 3, scripts decompile cleanly; for Godot 4, the bytecode is more compressed and decompilers may produce partial output.

---

## Anti-Cheat Considerations

Most Godot titles ship no anti-cheat. The indie norm. When AC is present, it's typically:

- **Steam-side**: VAC for Steam-released multiplayer titles. Detection is server-coordinated; the client has no AC driver.
- **Server-authoritative**: the server holds the authoritative state; client memory tampering does not affect the actual game outcome. Slay The Spire / Vampire Survivors style.
- **Soft-tamper-detect via PCK hash**: the engine checks if the embedded `.pck` has been modified; some titles cross-reference against an online manifest. Cosmetic, not enforced.

The export-template-modification path (changing the engine binary itself, repacking the `.pck`) is the most common modding path and is sometimes blocked by manifest checks. Memory-resident-only changes leave no trace on disk and are not caught by hash checks.

Cross-reference `knowledge/anti-cheat-architecture.md` for the AC ecosystem at large; Godot titles rarely appear there because they rarely ship kernel-level AC.

---

## Community Tools and Resources

Categories (no live URLs — search the named project):

- **gdsdecomp** — community GDScript bytecode decompiler; works well on Godot 3, partial on Godot 4. The standard tool for recovering script source from a compiled PCK.
- **godot-pck-explorer** — extract files from an embedded or standalone `.pck` archive (file-listing, single-file extract, full unpack).
- **Godot RE Tools (GodotREEngine)** — combined PCK extraction + GDScript decompilation in one project.
- **godot-cpp / GDExtension** — the official native-extension SDK. Useful for RE both as a *reference implementation* (how does the engine call into native code?) and as a *target* for writing your own integration (an in-game injected DLL that talks to the running engine).
- **Open-source upstream** — the largest resource. `github.com/godotengine/godot` tagged by version. Search the headers for any struct/function name you're reversing; the actual implementation is usually a few clicks away.
- **Godot debugger protocol** — Godot 4 supports remote debugging over TCP on port 6007 by default; the protocol is documented in the engine source. A live game launched with `--debug --remote-debug tcp://...` exposes the script-VM state for inspection.

---

## Cross-References

- `skill://anti-cheat-re` — kernel AC methodology (rarely needed for Godot titles, included for completeness)
- `skill://pcx-re-discipline` — RE discipline that applies to any binary
- `knowledge/anti-cheat-architecture.md` — broader AC reference (Godot rarely appears here)
- `knowledge/common-patterns.md` — Enma scripting patterns once you have the offsets you need
- `knowledge/offset-methodology.md` — sig derivation and validation
- `signatures/` — sig collections for other engines (no Godot subdirectory; the open-source headers serve that role)

---

## Source: `knowledge/engine-re-engine.md`

# RE Engine Reverse Engineering Reference

Engine-specific RE notes for Capcom's RE Engine (Resident Evil 2/3/4 remakes, RE7, RE Village, Devil May Cry 5, Monster Hunter Rise / Wilds, Street Fighter 6, Dragon's Dogma 2, Onimusha, Pragmata). Read this before attaching to an RE Engine title — the engine ships a reflected `via.*` type system with a managed-object layer that the community framework (REFramework) parses, which changes the workflow completely versus the pattern-scan grind of Frostbite or CryEngine. This fills the gap left by the UE/Unity/Source guides.

> **Read this before** doing memory analysis on any RE Engine title, and read `skill://authorized-security-research` first — Street Fighter 6 ships kernel-level anti-cheat and several titles ship Denuvo anti-tamper.

---

## Engine Overview

RE Engine is Capcom's in-house C++ engine and successor to MT Framework. Its defining feature is a built-in **reflection system** over a `via.*` type namespace, with a managed-object / singleton layer. The open-source **REFramework** hooks this reflection system and exposes it (plus a Lua scripting surface), which makes RE Engine the best-documented of the proprietary engines in this set — you can often query type and field layout from the engine itself rather than reverse it cold.

| Era | Representative titles |
|-----|-----------------------|
| 2017 | Resident Evil 7 |
| 2019 | RE2 Remake, Devil May Cry 5 |
| 2020–2021 | RE3 Remake, RE Village (RE8), Monster Hunter Rise |
| 2023–2024 | Street Fighter 6, RE4 Remake, Dragon's Dogma 2 |
| 2025+ | Monster Hunter Wilds, Onimusha: Way of the Sword, Pragmata, Kunitsu-Gami |

**Architecture summary:**

- **Custom renderer.** D3D11 / D3D12 backends. Camera and view live behind `via.Camera` / scene-view types.
- **GameObject-Component model with reflection.** The world is a `via.Scene` of `via.GameObject`s, each holding `via.Component`s. The spatial component is `via.Transform` (position / rotation / scale). Every type is described by a **reflection database** (TDB / type-definition table) — class names, field names, field offsets, and method signatures are all queryable at runtime.
- **Managed-object / singleton layer.** Gameplay systems are exposed as managed singletons (REFramework's `sdk.get_managed_singleton("app.…")` pattern). This is the access root: you fetch a system singleton, then walk its reflected fields.
- **Lua via REFramework, not native.** The engine itself is native C++; the Lua scripting surface is provided by REFramework's hook, not shipped by Capcom. The native reflection metadata, however, *is* Capcom's and is the thing REFramework reads.

**Notable quirks:**

- The **type database (TDB)** is the killer feature: instead of `struct_dump`-guessing field offsets, you can resolve a field by name through the reflection system. Find the TDB and field discovery becomes lookup, not search.
- Coordinate convention is commonly **Y-up** with `via.vec3` / `via.mat4` (column-major math in the engine's math types) — but axis handedness and matrix-major order **must be verified empirically** per title; do not assume.
- Many titles ship a **community modding base** (REFramework + EMV/Enhanced Model Viewer Lua mods), so the loose-anti-tamper single-player titles are heavily documented.

---

## Games Using This Engine

Grounded in commonly-known facts. Anti-cheat / anti-tamper column is "publicly associated with the title," generalize where uncertain.

| Game | Notes | Anti-Cheat / Anti-Tamper | Community SDK / modding base |
|------|-------|--------------------------|------------------------------|
| RE2 Remake | Single-player; heavily modded | Denuvo (early), Capcom anti-tamper | REFramework + EMV Engine |
| RE3 Remake | Single-player | Denuvo / Capcom anti-tamper | REFramework |
| RE4 Remake | Single-player + Mercenaries | Denuvo / Capcom anti-tamper | REFramework |
| RE Village (RE8) | Single-player | Denuvo + Capcom DRM (notable stutter) | REFramework |
| RE7 | Single-player | Denuvo | REFramework |
| Devil May Cry 5 | Single-player | Denuvo (early) | REFramework |
| Monster Hunter Rise | Co-op; loose anti-tamper | Denuvo (early) / server checks | REFramework |
| Monster Hunter Wilds | Co-op multiplayer | Server-side + anti-tamper | REFramework (community) |
| Street Fighter 6 | Competitive multiplayer | Kernel-level anti-cheat | Limited (AC restricts) |
| Dragon's Dogma 2 | Single-player | Denuvo / Capcom anti-tamper | REFramework |

> The pattern: **single-player RE Engine titles have loose anti-tamper and rich REFramework modding**; competitive/online titles (Street Fighter 6) lock down hard. Confirm what is actually loaded for your build.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — the reflection database is precisely how you avoid hardcoding them.

- **Reflection / Type Database (TDB) — the master anchor.** A global structure cataloguing every reflected type: name, parent, fields (name + type + offset), and methods. Resolving "the position field of the player transform" becomes: find the type by name → find the field by name → read its offset. This is what REFramework exposes; reversing it once gives you a name-based field resolver for the whole game.

- **Managed singletons.** Gameplay systems are reachable as named managed singletons (`app.*` types). The singleton table is itself reflected. From a system singleton you walk reflected fields to reach the player, the enemy list, etc.

- **Scene / GameObject / Component.**

```cpp
// Illustrative — resolve real offsets via the TDB, never hardcode
struct via_Scene {
    // holds the active GameObject set for the level
};
struct via_GameObject {
    // name, folder, component list; Transform is a component
};
struct via_Transform {       // via.Transform component
    // world position (via.vec3 / via.mat4), rotation (quat), scale
};
```

- **Player / enemy access.** Through an `app.*` gameplay system singleton → player GameObject → `via.Transform` for position, plus title-specific components for health/state. Enemy/NPC lists hang off the relevant manager singleton. Names of all of these come from the TDB.

- **Camera.** `via.Camera` / scene main-view exposes the view and projection matrices and FOV used for world-to-screen. Read the matrix and verify major order/axis before projecting.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit. On RE Engine you typically need **far fewer raw sigs** than on other engines because the TDB resolves most fields by name.

```
Type Database (TDB) pointer
Description: MOV/LEA reg, [rip+????] loading the global reflection database,
             referenced by every reflected type/field lookup.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01        (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → TDB root
Anchor tip:  xref reflected-type name strings ("via.", "app.") or the
             reflection init path; REFramework's TDB-locate logic documents the
             anchor shape for the current engine revision.
```

```
Managed singleton table
Description: LEA reg, [rip+????] loading the singleton container before a
             get-managed-singleton style lookup.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B    (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
```

```
Scene / main camera
Description: reference to the scene-manager / main-view singleton.
Anchor tip:  xref "via.Scene" / "via.Camera" type strings to the manager that
             owns the active scene and main camera.
```

**Anchor-string strategy (uniquely strong on RE Engine):** the engine literally ships its reflected type names (`via.Transform`, `app.PlayerManager`, etc.) as strings the reflection system uses. Xref those strings to reach the TDB and singleton machinery — then let the reflection system hand you field offsets by name instead of scanning for each one.

---

Once the TDB is anchored, the productive primitive is a **name→offset lookup**, not another byte scan. Conceptually: walk the TDB type list to the type whose name matches (`app.PlayerManager`, `via.Transform`, …), then walk its field list to the field whose name matches, and read the field's stored offset. REFramework implements exactly this; reproducing its TDB-walk for the current engine revision gives you the resolver everything downstream depends on.

### Verifying and Maintaining Sigs

Every sig must produce exactly one hit in its owning module, or the resolved address is meaningless. Scan, count, and extend:

```cpp
// Confirm a sig is unique before trusting its RIP resolution.
array<uint64> hits = p.find_all_code_patterns(g_base, g_size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
    // > 1: extend the sig with more surrounding bytes until unique.
    // 0  : the function was recompiled — re-derive from a fresh string xref.
}
```

On RE Engine you maintain **far fewer sigs than on other engines** — typically just the TDB-locate and singleton-table patterns. Once those resolve, field discovery is a TDB name lookup that does not depend on any byte pattern, so a patch that moves code rarely breaks downstream field access. Keep the two structural sigs anchored to `via.`/`app.` type-name strings, and let REFramework's per-revision TDB handling be your reference when the engine version changes.

## Reversal Workflow

Recommended first 60 minutes on an unknown RE Engine build:

1. **Confirm it is RE Engine.** `via.*` / `app.*` type strings in the binary, a single game executable, and the characteristic reflection-init code path confirm it. REFramework loading cleanly is also a strong signal.
2. **Locate the Type Database (TDB) first.** Everything else is a name-lookup once you have it. Use the reflected-type-name xref anchor; REFramework's open source is the reference for the current TDB layout/version.
3. **Enumerate managed singletons** and read their type names from the TDB — this maps the gameplay systems (player manager, enemy manager, camera) by name.
4. **Resolve the player Transform by field name** through the TDB rather than `struct_dump`-guessing. Read your own position to confirm.
5. **Find `via.Camera`** and read the view/projection matrix; **project a known point and verify on screen** before trusting axis/major order.
6. **Tooling.** REFramework first — it exposes the reflection system live and is the fastest path to field layout. IDA/Ghidra for the TDB/singleton machinery and for anything REFramework cannot reach. The TDB makes RE Engine the one engine here where name-based resolution largely replaces opcode sigs.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Street Fighter 6 → kernel-level anti-cheat.** A competitive title with a ring-0 anti-cheat component; treat it with the same caution as the kernel ACs in `anti-cheat-architecture.md` (foreign-module, integrity, and handle scanning). REFramework-style in-process hooking is the wrong tool against a protected competitive title.
- **RE2/3/4 Remake, RE Village, RE7 → Denuvo + Capcom anti-tamper.** Denuvo is **DRM/anti-tamper, not anti-cheat** — it resists static patching and unpacking, not memory reads from an authorized session. RE Village's DRM stack was notable for performance impact. These are single-player; there is no kernel AC watching memory access.
- **Monster Hunter Rise / Wilds → server-side checks + anti-tamper,** not a kernel AC of the EAC/BattlEye class on PC in the general case. Co-op state is server-authoritative.
- **Engine-specific surface:** the reflection/managed layer is an in-process attack surface. The very thing that makes single-player RE Engine titles easy to mod (loose anti-tamper + REFramework hooking the reflection system) is exactly what a hardened competitive title (SF6) shuts down. Never assume the REFramework approach that works on RE4 works on SF6.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **REFramework** (praydog, open source) — the central modding/RE base for RE Engine. Hooks the engine, exposes the reflection system and a Lua scripting surface, and documents TDB/singleton layout per engine revision. Single best resource for this engine.
- **EMV Engine** (Enhanced Model Viewer) — REFramework Lua mod that surfaces GameObjects, components, and field values live; effectively a runtime struct browser.
- **RE Engine modding communities** — REFramework script repositories and modding wikis documenting `app.*` system names per title.
- **TDB dumpers** — community tools that dump the full type database (types, fields, offsets) for a build, giving you a name→offset table.
- **IDA / Ghidra** — for the TDB and singleton machinery and anything outside REFramework's reach.

---

## Coordinate System and World-to-Screen

RE Engine math uses `via.vec3` / `via.mat4`; the convention is commonly **Y-up** with column-major math in the engine's math types. As everywhere, confirm axis handedness and matrix-major order empirically — read the `via.Camera` matrix and project a known point first.

```cpp
// Sketch — project through the via.Camera view-projection (Enma-style).
// Resolve the matrix field by NAME via the TDB rather than a raw offset where possible.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z
              + p.rf32(vp_addr + 60);
    if (w < 0.001) return false;                 // behind camera (guideline 10)
    float64 inv_w = 1.0 / w;
    float64 nx = (p.rf32(vp_addr + 0) * world.x + p.rf32(vp_addr + 16) * world.y
               +  p.rf32(vp_addr + 32) * world.z + p.rf32(vp_addr + 48)) * inv_w;
    float64 ny = (p.rf32(vp_addr + 4) * world.x + p.rf32(vp_addr + 20) * world.y
               +  p.rf32(vp_addr + 36) * world.z + p.rf32(vp_addr + 52)) * inv_w;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

> UNVERIFIED for any specific build. RE Engine's column-major math may require transposing the index mapping above — verify against your target.

## Offset Stability Reference

Where the key values typically live. On RE Engine, the reflection database makes most of these **name-resolvable**, which is far more stable than any raw offset.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| Type Database (TDB) | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; name→offset resolver |
| Managed singleton table | Sig + RIP / off TDB machinery | High | `app.*` system enumeration |
| `app.*` gameplay system | Singleton by name | High (by name) | Player / enemy managers |
| `via.Scene` | Scene-manager singleton | High (by name) | Active GameObject set |
| `via.GameObject` component list | Per-object, name-resolved | High (by name) | Find `via.Transform` here |
| `via.Transform` position | TDB field lookup by name | High (by name) | `via.vec3`, Y-up |
| Player / enemy state fields | TDB field lookup by name | High (by name) | Title-specific components |
| `via.Camera` view / projection | Scene main-view | Medium | Verify major order before W2S |

**Rules of thumb:**
- Find the **TDB first**; after that, resolve fields by name, not by hardcoded offset — this survives patches that a numeric offset would not.
- Only the TDB-locate and singleton-table sigs need raw pattern scanning; everything downstream is a name lookup.
- Cross-check field names against REFramework's known type list for the engine revision.

## Engine / Build Identification

Confirm you are on RE Engine before applying any of the above:

- **Module list** (`p.get_module_list()`): a single game executable; REFramework loading cleanly is a strong positive signal.
- **String markers:** reflected type names with `via.` and `app.` prefixes (`via.Transform`, `via.Scene`, `app.PlayerManager`-style) are unique to RE Engine and are also your TDB anchors.
- **Engine revision:** the TDB layout/version changes across titles (RE2 Remake vs Dragon's Dogma 2 vs Monster Hunter Wilds) — match REFramework's per-title TDB handling to your build.
- **AC posture tells you the approach:** a single-player title (loose anti-tamper + REFramework) is name-resolvable live; a competitive title (Street Fighter 6, kernel AC) is not — identify the title's posture before choosing tooling.

## Common Pitfalls

- **Reversing fields cold instead of using the TDB.** The whole point of RE Engine is name-based resolution. `struct_dump`-guessing field offsets when the reflection database can hand you the offset by name is wasted effort that also breaks every patch.
- **Hardcoding offsets the TDB would resolve.** A numeric offset dies on the next update; a TDB name lookup survives it. Hardcode nothing the reflection system can name.
- **Assuming column-major math is fine in a row-major projection.** RE Engine's `via.mat4` is column-major; if you copy a row-major W2S and points are wrong, transpose the index mapping.
- **Treating Denuvo as anti-cheat.** Denuvo on the RE remakes is anti-tamper/DRM — it resists static patching, not authorized-session memory reads. It is not a reason in itself that a memory approach fails.
- **Carrying the REFramework approach to Street Fighter 6.** SF6 ships kernel anti-cheat; the in-process reflection hooking that works on single-player titles is the wrong tool against a protected competitive game.
- **Mismatching the TDB version.** The type-database layout changes across titles (RE2 Remake vs Dragon's Dogma 2 vs Monster Hunter Wilds). Use the REFramework handling for *your* build's engine revision.
- **Skipping the position correctness check.** After resolving `via.Transform` position by name, read your own position and move in-game to confirm axis mapping before trusting it.

## Cross-References

- `knowledge/anti-cheat-architecture.md` — kernel-AC model to apply to Street Fighter 6.
- `knowledge/game-targets.md` — engine-by-game cross-reference style.
- `knowledge/offset-methodology.md` — RIP resolution and the sig-vs-hardcode discipline; note the TDB lets you prefer name-based resolution here.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved fields into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_quat_fl32`, `read_mat4_fl32`, `find_code_pattern`, `rs`/`rws` for reading TDB type-name strings.
- `skill://anti-cheat-re` — six-step AC methodology for Street Fighter 6.
- `skill://authorized-security-research` — scope/authorization before touching a protected build.
- If you derive stable patterns or a TDB-locate sig, add a stub under `signatures/re-engine/` mirroring `signatures/unreal-engine/`.

---

## Source: `knowledge/engine-redengine.md`

# REDengine Reverse Engineering Reference

Engine-specific RE notes for CD Projekt Red's REDengine (Cyberpunk 2077 on REDengine 4, The Witcher 3 on REDengine 3). Read this before attaching to a REDengine title — its RTTI/reflection system, REDscript gameplay VM, and fixed-point world-coordinate quirk differ from Unreal/Unity/Source, and the community framework (RED4ext / Cyber Engine Tweaks) exposes the engine's reflection much like REFramework does for RE Engine. This fills the gap left by the UE/Unity/Source guides.

> **Read this before** doing memory analysis on a REDengine title. **Note:** CDPR's future games (The Witcher 4, "Project Polaris") move to **Unreal Engine 5** — for those, use `signatures/unreal-engine/ue-reversal-guide.md`, not this file. REDengine knowledge applies to Cyberpunk 2077 and Witcher 3 only.

---

## Engine Overview

REDengine is CD Projekt Red's in-house C++ engine. Like RE Engine, it ships an **RTTI / reflection system** describing game classes, fields, and methods, plus a gameplay **scripting VM**. The community framework **RED4ext** hooks the engine and **Cyber Engine Tweaks (CET)** exposes the reflection system over Lua — so, as with RE Engine, you can often query type/field layout from the engine rather than reverse it cold. Both titles are single-player, which keeps anti-tamper loose and documentation rich.

| Generation | Era | Title |
|------------|-----|-------|
| REDengine 1 | 2011 | The Witcher 2 |
| REDengine 3 | 2015 | The Witcher 3: Wild Hunt |
| REDengine 4 | 2020 | Cyberpunk 2077 |
| (successor) | future | **Witcher 4 / Project Polaris → Unreal Engine 5** (not REDengine) |

**Architecture summary:**

- **Custom renderer.** D3D12 (Cyberpunk) with a deferred path; camera/view exposed through the engine's camera system.
- **RTTI / reflection system.** REDengine describes its classes through an RTTI database (class names, field names + offsets, method signatures). CET reads this to expose game classes by name — the same name-based-resolution advantage RE Engine's TDB gives.
- **Gameplay scripting VM.** The Witcher 3 uses **WitcherScript** (`.ws`); Cyberpunk 2077 uses **REDscript** plus a quest/scene scripting layer. Cyberpunk's gameplay objects are reached through a `GameInstance` and a set of game systems (`gamePlayerSystem`, scripting-exposed systems). RED4ext hooks the native side; redscript compiles to the gameplay VM.
- **Entity / world model.** `GameInstance` → game systems → the local player puppet (the controlled `gameObject`/`Entity`), with the world's NPC/entity set reachable through the relevant game system. Names of these come from the reflection database / CET.

**Notable quirks:**

- **Fixed-point world coordinates.** Cyberpunk's open world uses a high-precision world-position representation (an integer/fractional `WorldPosition`-style encoding) in places to avoid float drift over a large map. Do not assume a plain `float32` `Vec3` everywhere — confirm whether a given position field is float or the fixed-point world type before doing math on it.
- **Coordinate convention** is commonly **Z-up, right-handed** for Cyberpunk's world space (vehicles, navigation, world geometry are Z-up). Verify axis and matrix-major order empirically per build before committing world-to-screen math.
- **Reflection-first, like RE Engine.** Prefer resolving fields by name through the RTTI database (via CET / RED4ext knowledge) over `struct_dump`-guessing.

---

## Games Using This Engine

Grounded in commonly-known facts. Both shipped titles are single-player.

| Game | Engine | Notes | Anti-Cheat / Anti-Tamper | Community SDK / modding base |
|------|--------|-------|--------------------------|------------------------------|
| Cyberpunk 2077 | REDengine 4 | Single-player; reflection + REDscript | None (SP); Denuvo dropped post-launch on some platforms | RED4ext, redscript, Cyber Engine Tweaks (CET), TweakXL, ArchiveXL |
| The Witcher 3: Wild Hunt | REDengine 3 | Single-player; WitcherScript | None (SP); GOG/Steam DRM only | Modding community (script + WolvenKit-era tools) |
| The Witcher 2 | REDengine 1 | Single-player; legacy | None (SP) | — |
| Witcher 4 / Project Polaris | **Unreal Engine 5** | Future titles; not REDengine | — | Use the UE guide |

> Because both shipped REDengine titles are single-player with no anti-cheat, REDengine is the loosest anti-tamper of the four engines in this coverage pack — which is why the RED4ext/CET modding ecosystem is so mature. None of that freedom transfers to the UE5 successors.

---

## Memory Layout Patterns

Typical shapes. **All offsets vary per build** — the RTTI/reflection database is how you avoid hardcoding them.

- **RTTI / reflection database — the master anchor.** A global structure cataloguing reflected classes: name, parent, fields (name + type + offset), methods. Locating it gives you a name→offset resolver for the whole game, exactly as CET uses. This is the highest-value first target.

- **`GameInstance` and game systems.** The gameplay root. From `GameInstance` you reach game systems (e.g. a player system) by type; the player system hands you the local player puppet:

```cpp
// Illustrative — resolve real offsets via the reflection DB, never hardcode
struct GameInstance {
    // holds/owns the registered game systems
};
struct gamePlayerSystem {
    // local player puppet accessor: GetLocalPlayerControlledGameObject()-style
};
struct gameObject_Entity {
    // components: transform/placement (position), health/stats, etc.
};
```

- **Local player position.** Read off the player puppet's placement/transform component. **Check whether the field is a `float32` Vec3 or the fixed-point `WorldPosition` type** — Cyberpunk mixes both depending on the system. Convert the fixed-point form to world units before projecting.

- **NPC / entity enumeration.** Through the relevant world/entity game system rather than a single flat array. Names of the system and its container come from the reflection database / CET dumps.

- **Camera.** The engine's camera system exposes the view and projection used for world-to-screen. Read the matrix and verify major order / Z-up handedness before projecting.

---

## Common Sigs and RIP Patterns

Illustrative shapes only — same construction and resolution rules as `signatures/source-engine/common-sigs.md`. Wildcard the 4-byte RIP displacement, then `resolve_rip(hit, disp_offset, insn_len)`; re-derive per build; verify exactly one hit. As on RE Engine, the reflection DB resolves most fields by name, so you need fewer raw sigs.

```
RTTI / reflection database
Description: MOV/LEA reg, [rip+????] loading the reflection database root,
             referenced by every reflected class/field lookup.
Sig shape:   48 8B 0D ?? ?? ?? ?? 48 8B 01        (MOV RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7) → reflection DB root
Anchor tip:  xref reflected class-name strings ("game", "ent", "world" prefixes)
             or the RTTI init path; RED4ext's open source documents the anchor
             shape for the current game version.
```

```
GameInstance / game-systems container
Description: LEA reg, [rip+????] loading the GameInstance before a
             get-game-system style lookup.
Sig shape:   48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B   (LEA RCX, [rip+????])
Resolution:  resolve_rip(hit, disp_offset=3, insn_len=7)
```

```
Player system / local puppet
Description: reference to the player system that resolves the controlled puppet.
Anchor tip:  xref player-system / "GetLocalPlayerControlledGameObject" style
             reflected method-name strings to reach the accessor.
```

```
Camera / view system
Description: reference to the camera system exposing the active view + projection.
Anchor tip:  xref camera-system reflected type/method names to reach the matrix
             the renderer composes per frame; read it out and verify Z-up /
             major order before projecting.
```

**Anchor-string strategy:** REDengine ships its reflected class and method names as strings the RTTI system consumes. Xref those to reach the reflection DB and `GameInstance`, then resolve fields by name. RED4ext / CET open source is the authoritative reference for the current game version's anchors — lean on it rather than blind opcode scanning.

---

Once the reflection DB is anchored, the productive primitive is a **name→offset lookup** rather than another byte scan: walk the reflected class list to the class whose name matches (e.g. the player puppet type), then its property list to the named field, and read the stored offset. CET exposes this live over Lua and RED4ext implements the native walk — reproducing it for the current build gives you the resolver the rest of the workflow depends on. This is also where you classify a position property as `float32` versus fixed-point `WorldPosition` from its reflected type.

### Verifying and Maintaining Sigs

Every sig must produce exactly one hit in its owning module, or the resolved address is meaningless. Scan, count, and extend:

```cpp
// Confirm a sig is unique before trusting its RIP resolution.
array<uint64> hits = p.find_all_code_patterns(g_base, g_size, sig);
if (hits.length() != 1) {
    println(format("WARNING: sig has {d} hits, expected 1", hits.length()));
    // > 1: extend the sig with more surrounding bytes until unique.
    // 0  : the function was recompiled — re-derive from a fresh string xref.
}
```

As on RE Engine, you maintain **only a couple of structural sigs** — the reflection-DB-locate and `GameInstance` patterns. Downstream field access is name resolution through the reflection database, so it largely survives code-moving patches. RED4ext/CET track the current build's anchors; keep your two sigs recorded against their `game`/`ent`/`world` class-name string anchors so the offset-maintainer can rebuild them after an update.

## Reversal Workflow

Recommended first 60 minutes on a REDengine build (Cyberpunk 2077 / Witcher 3):

1. **Confirm it is REDengine — and not a UE5 successor.** Cyberpunk ships a single `Cyberpunk2077.exe` with reflected `game*`/`ent*`/`world*` class strings and the REDscript/quest VM. If you are on a future CDPR title, check for UE markers (`*-Win64-Shipping.exe`, `GObjects` machinery) and switch to the UE guide.
2. **Locate the RTTI / reflection database first.** It turns field discovery into name lookup. Use the class-name xref anchor; RED4ext source is the reference for the current layout.
3. **Reach `GameInstance` and enumerate game systems** by name from the reflection DB — this maps player, world, and camera systems.
4. **Resolve the local player puppet** via the player system, then its placement/transform. **Determine float vs. fixed-point `WorldPosition`** before doing position math; read your own position to confirm.
5. **Find the camera** and read view/projection; **project a known world point and verify on screen** before trusting axis/major order.
6. **Tooling.** RED4ext + CET first — CET exposes the reflection system live (browse classes/fields/methods by name) and is the fastest path to layout. IDA/Ghidra for the reflection DB and `GameInstance` machinery and anything the frameworks cannot reach. Name-based resolution largely replaces opcode sigs here.

---

## Anti-Cheat Considerations

Cross-reference `knowledge/anti-cheat-architecture.md`. Guidance level only.

- **Cyberpunk 2077 and The Witcher 3 → no anti-cheat.** Both are single-player. Cyberpunk shipped with Denuvo on some storefronts and later dropped it; Denuvo is **DRM/anti-tamper, not anti-cheat** — it resists static patching, not memory reads from an authorized session. There is no kernel AC monitoring memory access on these titles.
- **Loose anti-tamper → mature modding.** The absence of anti-cheat is precisely why RED4ext/CET can hook the engine in-process and expose the reflection system. This is engine-and-title-specific freedom.
- **Future UE5 titles will differ.** CDPR's Witcher 4 / Project Polaris move to Unreal Engine 5; if any future title is multiplayer it will ship its own anti-cheat. Do not carry REDengine assumptions forward — treat the UE5 successors as standard UE targets under whatever AC they ship.
- **Engine-specific surface:** the REDscript/quest VM and the reflection system are in-process surfaces that the modding frameworks use; on a single-player title there is no AC watching them, but that is a property of the title, not a guarantee.

---

## Community Tools and Resources

Refer to categories by name; search for current sources yourself. No live cheat-distribution links.

- **RED4ext** (open source) — the native hooking framework for Cyberpunk 2077; the RE Engine of CDPR's world. Documents reflection-DB and `GameInstance` layout per game version.
- **Cyber Engine Tweaks (CET)** — exposes the reflection system over Lua: browse and call reflected classes/methods/fields by name live. Effectively a runtime type/field browser, the fastest layout-discovery tool for Cyberpunk.
- **redscript / WitcherScript tooling** — gameplay-script compilers/decompilers; useful for understanding which systems own which state.
- **WolvenKit** — modding toolkit for REDengine asset/archive editing; structural reference for the engine's data model (asset side, not memory).
- **TweakXL / ArchiveXL** — data/record extension frameworks; reference for how game records and systems are named.
- **IDA / Ghidra** — for the reflection DB and `GameInstance` machinery and anything outside the frameworks.

---

## Coordinate System and World-to-Screen

Cyberpunk's world space is commonly **Z-up, right-handed**. The defining hazard is the **fixed-point `WorldPosition` encoding** used to keep precision across a large open world: a position field may be a plain `float32` `Vec3` *or* an integer/fractional world type. Decode the fixed-point form to world units before any projection math, and verify axis/major order by reading the camera matrix and projecting a known point.

```cpp
// Sketch — project through the camera view-projection (Enma-style).
// Resolve fields by NAME via the reflection DB where possible. Confirm the
// position field is float32 vs fixed-point BEFORE calling this.
bool world_to_screen(proc_t& p, uint64 vp_addr, vec3 world, vec2& screen) {
    float64 w = p.rf32(vp_addr + 12) * world.x
              + p.rf32(vp_addr + 28) * world.y
              + p.rf32(vp_addr + 44) * world.z   // Z is vertical on REDengine
              + p.rf32(vp_addr + 60);
    if (w < 0.001) return false;                 // behind camera (guideline 10)
    float64 inv_w = 1.0 / w;
    float64 nx = (p.rf32(vp_addr + 0) * world.x + p.rf32(vp_addr + 16) * world.y
               +  p.rf32(vp_addr + 32) * world.z + p.rf32(vp_addr + 48)) * inv_w;
    float64 ny = (p.rf32(vp_addr + 4) * world.x + p.rf32(vp_addr + 20) * world.y
               +  p.rf32(vp_addr + 36) * world.z + p.rf32(vp_addr + 52)) * inv_w;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

> UNVERIFIED for any specific build. If world positions are stored fixed-point, feeding them raw into this projection produces garbage — decode first.

## Offset Stability Reference

Where the key values typically live. As on RE Engine, the reflection database makes most of these **name-resolvable**, which beats any raw offset for patch survival.

| Value | Reached via | Stability | Notes |
|-------|-------------|-----------|-------|
| RTTI / reflection DB | Module data section, sig + RIP | None (address) / High (sig) | Master anchor; name→offset resolver |
| `GameInstance` | Sig + RIP / off reflection machinery | High | Game-systems container |
| Player system (`gamePlayerSystem`) | Game system by name | High (by name) | Resolves local puppet |
| Local player puppet | Player-system accessor | High (by name) | `gameObject`/`Entity` |
| Puppet placement / transform | Reflection field by name | Medium | Float32 `Vec3` **or** fixed-point `WorldPosition` |
| Puppet stats / health | Reflection field by name | High (by name) | Stat-pool component |
| NPC / entity set | World/entity game system | Medium | Not a single flat array |
| Camera view / projection | Camera system | Medium | Verify Z-up / major order before W2S |

**Rules of thumb:**
- Find the **reflection DB first**; resolve downstream fields by name. RED4ext/CET source documents the current build's anchors.
- Only the reflection-DB-locate and `GameInstance` sigs need raw pattern scanning.
- Always classify a position field (float vs fixed-point) before doing distance/W2S math — this is the REDengine-specific footgun.

## Engine / Build Identification

Confirm you are on REDengine — **and not a UE5 successor** — before applying any of the above:

- **Module list** (`p.get_module_list()`): `Cyberpunk2077.exe` (a single large executable); RED4ext/CET loading cleanly is a strong positive signal. If you see `*-Win64-Shipping.exe` or UE `GObjects` machinery, you are on a UE5 title → use the UE guide.
- **String markers:** reflected class names with `game`, `ent`, `world` prefixes, REDscript/quest-VM strings, and CET-known method names.
- **Title:** only Cyberpunk 2077 (REDengine 4) and Witcher 3 (REDengine 3) apply here; Witcher 4 / Project Polaris are Unreal Engine 5.
- **AC posture:** both shipped titles are single-player with no anti-cheat, so in-process reflection access (CET/RED4ext) is viable — a property of the title, not transferable to any future protected build.

## Common Pitfalls

- **Feeding fixed-point `WorldPosition` into float math.** The defining REDengine footgun: a position field may be integer/fractional fixed-point, not a `float32` `Vec3`. Classify every position field and decode the fixed-point form to world units before distance or W2S math.
- **Reversing fields cold instead of using the reflection DB.** Like RE Engine, REDengine is name-resolvable via RTTI. CET/RED4ext expose classes/fields/methods by name — use them rather than `struct_dump`-guessing offsets that die each patch.
- **Mistaking a UE5 successor for REDengine.** Witcher 4 / Project Polaris are Unreal Engine 5. Confirm the executable and reflection strings; if you see UE `GObjects` machinery, switch to the UE guide entirely.
- **Assuming Y-up.** Cyberpunk world space is Z-up; ported Y-up math swaps the wrong axis.
- **Expecting an anti-cheat that is not there (or assuming one never will be).** The shipped titles are single-player with no AC — but that freedom is title-specific and does not carry to any future protected CDPR build.
- **Treating Denuvo as a memory-access blocker.** Where present, Denuvo is anti-tamper/DRM; some Cyberpunk versions dropped it entirely. It does not stop authorized-session reads.
- **Skipping the position correctness check.** After resolving the puppet placement by name, read your own position and move in-game to confirm both the axis mapping and the float-vs-fixed-point classification.

## Cross-References

- `signatures/unreal-engine/ue-reversal-guide.md` — **use this for CDPR's future UE5 titles**, not the REDengine notes here.
- `knowledge/anti-cheat-architecture.md` — AC model for any future multiplayer CDPR title.
- `knowledge/game-targets.md` — engine-by-game cross-reference style.
- `knowledge/offset-methodology.md` — RIP resolution and sig-vs-hardcode discipline; prefer name-based resolution via the reflection DB here.
- `knowledge/common-patterns.md` — entity-iteration, world-to-screen, GUI patterns for wiring resolved fields into a script.
- `signatures/source-engine/common-sigs.md` — `resolve_rip` helper and uniqueness verification.
- `knowledge/pcx-api-cheatsheet.md` — `read_vec3_fl32`, `read_mat4_fl32`, `find_code_pattern`, `rs`/`rws` for reading reflected class-name strings; note the fixed-point `WorldPosition` needs manual decode, not a typed read.
- `skill://authorized-security-research` — scope/authorization (relevant for any future protected CDPR title).
- If you derive stable patterns or a reflection-DB-locate sig, add a stub under `signatures/redengine/` mirroring `signatures/unreal-engine/`.

---

## Source: `knowledge/enma-cheatsheet.md`

# Enma Language Quick Reference

## Primitives

| Type | Size | Notes |
|------|------|-------|
| `bool` | 1B | `true` / `false` |
| `char` / `wchar` | 1B / 2B | ASCII / wide |
| `int8/16/32/64` | 1-8B | Signed |
| `uint8/16/32/64` | 1-8B | Unsigned |
| `aint8/16/32/64` | 1-8B | Atomic |
| `float32` / `float64` | 4B / 8B | IEEE single/double |
| `string` / `wstring` | ptr | UTF-8 / UTF-16 heap |
| `void` / `null` / `auto` | - | No value / null literal / inferred |

## Conversion Rules (COMPILE-TIME ENFORCED)

- `signed ↔ unsigned` → **COMPILE ERROR** — use `cast<uint64>(x)`
- `float → int` → **COMPILE ERROR** — use `cast<int32>(f)`
- `int → float` → implicit OK
- `float32 → float64` → implicit OK
- `float64 → float32` → **COMPILE ERROR** — use `cast<float32>(d)`
- `pointer ↔ int64/uint64` → implicit (both 8-byte)

## Conventions (official Enma overview)

> Source: [Perception Enma — Overview](https://docs.perception.cx/perception/enma) → *Conventions*.
> Mirror in this repo: [`docs/perception/readme.md`](../docs/perception/readme.md).

- **Colors and positions — always wrap.** `color(255, 255, 255, 255)`, `vec2(10.0, 20.0)`. Freshly constructed each frame is fine; Enma drops the temporaries at scope exit. (See guideline #7.)
- **Float32 literals — use the `f` suffix.** `0.2f`, **not** `cast<float32>(0.2)`. A bare `0.2` is `float64`. Required for vertex buffers (the GPU cares). This is guideline #8 and `script-linter.py` rule 8. Reserve `cast<float32>(x)` for converting a `float64` *value* (variable/expression), not a literal.
- **Handles — opaque encrypted `int64`.** Every `create_*` / `load_*` native returns an encrypted `int64`. Pass it straight back into the matching `draw_*` / `bind_*` / `destroy_*` call. Don't inspect, print, arithmetic, or compare it to a raw integer.

```cpp
color white    = color(255, 255, 255, 255);   // wrap, fresh per frame is fine
color noeffect = color(0, 0, 0, 0);
vec2  pos      = vec2(40.0, 40.0);            // float64 literals by default

float32 uv_bias = 0.2f;                       // f suffix -> float32 (vertex buffers)
int64  ticks    = 40;
float64 measured = cast<float64>(ticks);      // a float64 VALUE
float32 m32      = cast<float32>(measured);   // cast a value, not a literal

int64 tex = /* any create_* / load_* native */;  // encrypted handle — opaque
// Hand tex straight back to its matching draw_* / bind_* / destroy_* native.
// WRONG: if (tex == 0) ... ;  println(tex);  tex + 0x1000;
```

> **SDK:** Perception's Enma SDK is not public yet (per the same overview).

## Variables

```cpp
int32 x = 42;
const float64 PI = 3.14;           // runtime-initialized, not reassignable
constexpr int32 MAX = 100;          // compile-time only
auto y = x + 1;                     // inferred
nullable int32 n = null;            // can hold null
```

## Operators

Arithmetic: `+ - * / %`  |  Comparison: `== != < > <= >=`  |  Logical: `&& || !`
Bitwise: `& | ^ ~ << >>`  |  Compound: `+= -= *= /= %= &= |= ^= <<= >>=`
Inc/Dec: `++ --`  |  Ternary: `cond ? a : b`  |  Cast: `cast<T>(x)`
Size: `sizeof(T)` `offsetof(Struct, field)`  |  Heap: `new T(args)` `delete`

## Control Flow

```cpp
if (x > 0) { } else if (x == 0) { } else { }
while (x > 0) x--;
do { x++; } while (x < 10);
for (int32 i = 0; i < 10; i++) { }
for (int32 v : arr) { }                          // for-each
for (string k, int64 v : m) { }                  // map for-each
switch (x) { case 1: break; default: break; }
int32 r = match (x) { 1 => 10, 2 => 20, _ => 0 };
defer { cleanup(); }                              // runs at scope exit
goto label; label: /* ... */
```

## Functions

```cpp
int32 add(int32 a, int32 b = 10) { return a + b; }   // default param
void swap(int32& a, int32& b) { /* pass by ref */ }   // reference
bool parse(string s, out int32 v) { /* write-only out */ }
void log(string fmt, ...) { /* variadic */ }
auto fn = (int32 x) => x * 2;                         // lambda
auto fn2 = [&cap](int32 x) -> int32 { return cap + x; }; // closure
```

## Structs (value types) vs Classes (reference types)

```cpp
struct Vec2 { float64 x; float64 y; }   // stack-allocated, copied on assign
class Player {                            // heap-allocated via new, virtual dispatch
    int32 health;
    Player(int32 h) { health = h; }
    virtual void update() { }
}
interface IDrawable { void draw(); }
mixin Logging for Player { void log() { println("hp=" + cast<string>(health)); } }
```

## Templates

```cpp
template<typename T>
T max(T a, T b) { return a > b ? a : b; }
template<typename T>
struct Stack { T[] items; void push(T v) { items.push(v); } }
```

## Arrays & Maps

```cpp
int32[] arr = {1, 2, 3};
arr.push(4); arr.pop(); arr.sort(); arr.reverse();
arr.contains(2); arr.index_of(3); arr.slice(0, 2);
arr.length(); arr.remove(0); arr.insert(1, 99);

map<string, int64> m;
m["key"] = 42; m.get("key"); m.contains("key");
m.remove("key"); m.length();
```

## Strings

```cpp
string s = f"value={x}";                         // interpolation
string h = format("addr=0x{x} name={s}", addr, name);  // format
s.length(); s.substr(0, 5); s.find("abc");
s.contains("x"); s.starts_with("pre"); s.ends_with("suf");
s.to_upper(); s.to_lower(); s.trim(); s.replace("a","b");
s.split(","); s.to_int(); s.to_float();
```

## Pointers

```cpp
int32* p = new int32(42);    // heap alloc
int32 v = *p;                // dereference (shallow copy)
delete p;                     // free
int32 x = 5; int32* px = &x; // address-of
Player* pl = new Player(100);
pl->update();                 // member access via pointer
```

## Coroutines

```cpp
coroutine int32 counter() { int32 i = 0; while (true) { yield i; i++; } }
coroutine_t c = counter();
c.next(); int32 v = c.value();
```

## Exceptions

```cpp
try { throw "error"; }
catch (string e) { println(e); }
// dtors and defer blocks run during stack unwinding
```

## Modules & Preprocessor

```cpp
import "math";                    // import module
import "utils" as u;              // aliased
using namespace MyLib;            // bring names into scope

#define DEBUG
#ifdef DEBUG
  println("debug mode");
#endif
#include "shared.em"
```

## Annotations

```cpp
[[packed]] struct Data { uint8 a; uint32 b; }     // no padding
[[align(16)]] struct Aligned { float32 v[4]; }
[[reflect]] struct Config { int32 x; }             // queryable from host
[[dll("user32.dll")]] extern int32 MessageBoxA(/*...*/);  // FFI
[[noopt]] void sensitive() { }                      // skip optimization
[[export]] void api_func() { }                      // visible to host
```

---

## Source: `knowledge/game-targets.md`

# Perception.cx Game Support Reference

Every game with active scripts in the Perception.cx Script Market (as of June 2026), organized by category. This toolkit supports **AngelScript** (`AS`) and **Enma** only; market entries below are listed as AngelScript unless a project-specific Enma port is explicitly created.

> Counts are minimums (`N+`) — they reflect publicly listed market entries, not private/loader-only scripts.

## FPS / Battle Royale

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Counter-Strike 2 | Source 2 | 10+ | VAC | Official + community suite | AS |
| Apex Legends | Source (Respawn) | 5+ | EAC (EOS) | UFOHOOK, ATLAS, ARIEngine | AS |
| COD: Black Ops 7 / Warzone | IW Engine | 2+ | RICOCHET | — | AS |
| Fortnite | Unreal Engine | 1+ | EAC (EOS) | — | AS |
| PUBG (Steam) | Unreal Engine | 2+ | BattlEye | — | AS |
| Overwatch / Overwatch 2 | Custom | 3+ | Custom (Blizzard) | — | AS |
| The Finals | Embark / Theia | 2+ | EAC + Theia | — | AS |
| Deadlock | Source 2 | 2+ | VAC | — | AS |
| Arena Breakout Infinite | Unity | 3+ | EAC (EOS) | — | AS |
| BloodStrike | Unreal Engine | 1+ | EAC | — | AS |
| Farlight 84 | Unreal Engine | 1+ | EAC | — | AS |

## Survival / Open World

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Escape from Tarkov | Unity | 1+ | BattlEye | Official | AS |
| Rust | Unity | 2+ | EAC (EOS) | — | AS |
| DayZ | Enfusion | 1+ | BattlEye | — | AS |
| Scum | Unreal Engine | 1+ | EAC | — | AS |
| Ark: Survival Evolved | Unreal Engine | 1+ | BattlEye | — | AS |
| The Isle: Evrima | Unreal Engine | 1+ | EAC | — | AS |
| Dark and Darker | Unreal Engine | SDK | EAC (EOS) | SDK available | AS |

## Tactical / Team

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Rainbow Six Siege | AnvilNext | 1+ | BattlEye | Private | AS |
| Hunt: Showdown 1896 | CryEngine | 2+ | EAC (EOS) | — | AS |
| Marvel Rivals | Unreal Engine | 2+ | EAC (EOS) | — | AS |
| The Division 2 | Snowdrop | 1+ | EAC | — | AS |

## Horror / Other

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| Dead by Daylight | Unreal Engine | 1+ | EAC (EOS) | Official, Featured | AS |
| Chivalry 2 | Unreal Engine | 1+ | EAC | — | AS |
| Far Far West | Unknown | 1+ | Unknown | — | AS |
| KovaaK's | Unreal Engine | 1+ | None | Aim trainer | AS |
| GeoGuessr | Web / Steam | 1+ | None | — | AS |

## Modded / Custom Clients

| Game | Engine | Scripts | Anti-Cheat | Notable | Lang |
|------|--------|---------|-----------|---------|------|
| GTA V (RAGE:MP / ALT:V) | RAGE | 1+ | None (mod client) | Multiplayer mods | AS |
| Roblox | Custom | 1+ | Byfron (Hyperion) | Official | AS |

**Total: 29 supported games.**

## Engine Summary

| Engine | Games |
|--------|-------|
| Source 2 | CS2, Deadlock |
| Source (Respawn) | Apex Legends |
| Unreal Engine | Fortnite, PUBG, Dead by Daylight, Marvel Rivals, Arena Breakout Infinite, Scum, The Isle, Dark and Darker, Ark, Chivalry 2, KovaaK's, BloodStrike, Farlight 84 |
| IW Engine | COD: Black Ops 7 / Warzone |
| Unity | Escape from Tarkov, Rust, Arena Breakout Infinite |
| CryEngine | Hunt: Showdown 1896 |
| Enfusion | DayZ |
| AnvilNext | Rainbow Six Siege |
| Snowdrop | The Division 2 |
| Embark / Theia | The Finals |
| RAGE | GTA V |
| Custom / Other | Overwatch, Roblox, GeoGuessr, Far Far West |

> Arena Breakout Infinite appears under both Unreal Engine and Unity in market metadata; treat its engine as version-dependent and confirm at runtime via the module list.

## Engine-Specific Considerations

### Unreal Engine
- **Dumper required.** Object/name resolution goes through `GObjects` and `GNames`. Use an offset dumper (e.g. Dumper-7 / UE4SS output) and feed the resulting struct offsets into your script; do not hardcode across patches.
- **GWorld → GameInstance → PersistentLevel → Actors** is the canonical entity walk. Cache `GWorld` once per frame, then iterate the actor array.
- **FName** decoding needs the name pool. Resolve via `GNames` chunked array; class names come from `UObject::ClassPrivate->Name`.
- Coordinates are typically `FVector` (3×`float32`) — read with `read_vec3_fl32`. World-to-screen needs the camera `POV` (location + rotation + FOV) from the local player controller.

### Source 2 (CS2, Deadlock)
- **Schema system.** Field offsets are not static — they live in the runtime schema. Resolve member offsets via the `SchemaSystem` / `client.dll` schema classes (e.g. `C_CSPlayerPawn`) rather than fixed numbers.
- Entity list via `entity_list` / `CGameEntitySystem`; iterate identity chunks.
- View matrix is exposed in `client.dll` — pattern-scan for the `view_matrix` global; W2S is a straight `mat4` multiply (`read_mat4_fl32`).

### Source (Respawn — Apex)
- Heavily modified Source; entity walk differs from Valve Source. Use community offset tables; highlight pointers and entity list are pattern-scanned per build.

### Unity (Tarkov, Rust, ABI)
- **IL2CPP.** Managed code is AOT-compiled; use `il2cpp_dump` / Il2CppDumper to recover class and field metadata, then resolve via `GameAssembly.dll` + `global-metadata.dat`.
- Mono (legacy) builds expose typedefs directly via the Mono API; check which backend the title ships.
- Static fields are reached through the IL2CPP class' static field pointer; instance offsets come from the dumped metadata.

### IW Engine (COD)
- Aggressive anti-tamper and frequently rotating offsets; entity/bone access usually requires per-build pattern scans. Treat all offsets as volatile.

### CryEngine (Hunt) / Enfusion (DayZ) / AnvilNext (R6) / Snowdrop (Division 2)
- Proprietary entity systems with no public dumper. Rely on pattern scanning to anchor the entity list and local player, then map structs manually per build.

### RAGE (GTA V)
- Targeted via multiplayer mod frameworks (RAGE:MP, ALT:V). Entity pools (`CPed`, `CVehicle`) are reached through the replay/pool managers; scope is mod-client memory, not the base game.

### Custom / Web (Overwatch, Roblox, GeoGuessr)
- No shared tooling. Overwatch uses a bespoke engine (pattern-scan everything). Roblox runs its own VM — official script handles the surface. GeoGuessr is web/Steam wrapper, DOM/state-driven rather than classic memory ESP.

## Practical Workflow

1. **Identify the engine** — `p.get_module_list()` reveals the giveaways: `UnrealEditor`/`*-Win64-Shipping.exe` (UE), `client.dll` + `engine2.dll` (Source 2), `GameAssembly.dll` (Unity IL2CPP), `mono-2.0-bdwgc.dll` (Unity Mono).
2. **Get offsets** — dumper for UE/Unity, schema resolution for Source 2, pattern scans for proprietary engines.
3. **Anchor per frame** — cache the world/entity-list root once, then iterate; never re-scan inside the actor loop.
4. **Treat every offset as patch-volatile** — prefer schema/dumper resolution over literals so a game update doesn't silently corrupt reads.

---

## Source: `knowledge/gui-design-patterns.md`

# GUI Design Patterns

The Perception.cx sidebar GUI is a fixed-width vertical strip. Good layouts make features discoverable, tunings easy to find, and state visible at a glance. The 12 game-cheat-guidelines say "GUI for every tunable" (rule #11), but say nothing about how to lay it out well. This file fills that gap with section-organization patterns, widget order, label conventions, slider range discipline, hotkey conventions, color discipline, conditional widgets, state visibility, and the anti-patterns to avoid.

> **Read this before** designing a new feature's GUI section, or auditing an existing one. Pair with `templates/overlay-basic.em` (small example) and `templates/full-project/` (multi-feature example) for working code.

---

## Section Organization: One Feature Per Section

**Mirrors `game-cheat-guidelines` rule #6 (one feature per file). The GUI shape follows the code shape.**

The sidebar is composed of independent sections — `create_section("ESP")`, `create_section("Aimbot")`, `create_section("Radar")`. Each section is collapsible by the user. Users disable a feature *socially* by collapsing its section ("I'm not using radar today; collapse it"); mixing concerns inside one section defeats the affordance.

```cpp
// RIGHT — one feature per section
int64 sec_esp    = create_section("ESP");
int64 sec_aim    = create_section("Aimbot");
int64 sec_radar  = create_section("Radar");
int64 sec_misc   = create_section("Misc");

// WRONG — all features in one section
int64 sec_all = create_section("Features");  // user has to scroll past 40 widgets
```

The exception: tiny features (a single checkbox) that don't justify their own section header. Group them under a `Misc` section at the bottom. The rule is one *feature* per section, not one widget — a section with 6-10 widgets is normal.

**Why:** Collapsibility is the discoverability mechanism. Mixing makes the sidebar a wall of widgets that the user scans linearly; separating makes it a directory the user can collapse-and-skip.

---

## Widget Order Within a Section

**Canonical order: master toggle → hotkey → primary tuning → secondary tunings → color picker(s) → separator → status label.**

Users scan top-to-bottom. The widget order reflects the frequency of interaction: the master toggle is touched most often (turn the feature on/off), the status label is glanced at most often (is it working?). Put both where the eye naturally lands.

```cpp
int64 sec = create_section("ESP");

// 1. Master toggle — top of section, always.
section_checkbox(sec, "Enabled", g_esp_enabled);

// 2. Hotkey — the second-most-touched widget after the toggle.
section_keybind(sec, "Toggle hotkey", g_esp_hotkey);

// 3. Primary tuning — the most-used slider or combo.
section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");

// 4. Secondary tunings — less-frequent.
section_slider_float(sec, "Max distance", g_esp_max_dist, 0.0, 500.0);
section_slider_int(sec, "Line thickness", g_esp_thickness, 1, 5);
section_checkbox(sec, "Show distance label", g_esp_show_dist);

// 5. Color pickers — group at the end so the color noise doesn't dominate.
section_color_picker(sec, "Friendly", g_esp_color_friendly);
section_color_picker(sec, "Enemy",    g_esp_color_enemy);

// 6. Separator — visually break "controls" from "diagnostics".
section_separator(sec);

// 7. Status label — what is the feature doing right now?
section_label(sec, "Drawing 12 entities (3 friendly, 9 enemy)");
```

(The status label text is updated each frame from the render routine — the API takes a `string`, so build it with `format(...)` against your cached counts.)

The order isn't sacred (a feature with no hotkey skips that slot), but the *gravity* is: most-touched at the top, diagnostics at the bottom.

**Why:** A GUI that lets the user find the toggle in 200ms is one they actually use. A GUI where the user has to scroll past four color pickers to find the toggle is one they fight with.

---

## Label Conventions

**Imperative for toggles, units in slider labels, no jargon.**

```cpp
// RIGHT — clear, scannable, action-oriented
section_checkbox(sec, "Show ESP", g_esp_enabled);
section_slider_float(sec, "Smoothing (frames)", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "Max distance (meters)", g_esp_max_dist, 0, 500);
section_combo(sec, "Target priority", g_target_mode, "Closest,Lowest HP,Crosshair");

// WRONG — past-tense, abbreviated, unit-less
section_checkbox(sec, "ESP enabled", g_esp_enabled);          // past-tense state
section_slider_float(sec, "SM", g_aim_smoothing, 0, 15);      // what is SM?
section_slider_int(sec, "Dist", g_esp_max_dist, 0, 500);      // dist in what?
section_combo(sec, "Pri", g_target_mode, "C,L,X");            // unreadable
```

Imperative phrasing reads as a button label: "Show ESP" / "Hide ESP" maps directly to the checkbox state. "ESP enabled" makes the user parse a sentence to know what clicking it does.

Units in slider labels save support questions. "Smoothing" is ambiguous (frames? seconds? ticks?). "Smoothing (frames)" is not.

Abbreviations are fine when they're industry-standard (FOV, ESP, HP, AC); not fine when they're project-internal (AB for aimbot, SM for smoothing). The rule of thumb: would a Discord support request use this abbreviation? If yes, ship it. If you'd have to expand it on first use in a support reply, expand it in the label.

**Why:** A label is the entire UX of a widget. A clear label is self-documenting; an unclear one needs a doc the user won't read.

---

## Slider Ranges: Useful, Not Possible

**Set min/max to the *useful* range, not the *possible* range. A smoothing slider's useful range is 0..15; setting it 0..1000 makes the useful range one pixel wide.**

The slider widget maps the entire visible track to the `[min, max]` interval. If the useful range is 0..15 and the slider is 0..1000, the user can only meaningfully tune in the first 1.5% of the track, and dragging past that produces values that don't change behavior (or, worse, crash).

```cpp
// WRONG — possible range, useless slider
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 1000.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 0, 10000);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 100000.0);

// RIGHT — useful range, every drag matters
section_slider_float(sec, "Smoothing", g_aim_smoothing, 0.0, 15.0);
section_slider_int(sec, "FOV (px)", g_aim_fov, 8, 400);
section_slider_float(sec, "Max distance (m)", g_max_dist, 0.0, 500.0);
```

How to pick useful ranges:

- Measure or estimate the *real* range your feature operates in (smoothing past 15 frames is sluggish; aimbot FOV past 400px is "aim at the whole screen").
- Add 20-50% headroom past the practical upper bound (the user might want to go higher than you expect).
- Set the minimum to the smallest sensible value (0 if the feature can be disabled by the slider; 1 if it needs at least some value to function).

When the truly useful range is dynamic (depends on game state — e.g. max-distance varies between a small arena and a large open world), pick a static range that covers the wider case and document it in a comment.

**Why:** A slider's value is the area where it's draggable. A 0..1000 slider for a 0..15 problem is a configuration error, not a feature.

---

## Defaults That Work for First-Time Users

**Ship the tuning a new user would want, not the tuning you've personally settled on.**

The first time a user loads the script, every widget has its default value. If the defaults are bad, the script appears broken and the user gives up before reaching the GUI to fix them.

| Widget | Bad default | Good default |
|---|---|---|
| `g_esp_enabled` | `false` (user has to find the toggle) | `true` (user sees the feature immediately) |
| `g_esp_color` | `color(0, 0, 0, 255)` (invisible on dark UI) | `color(255, 50, 50, 255)` (red, contrasts with most game UIs) |
| `g_aim_smoothing` | `0.0` (instant snap — detection vector + jarring) | `8.0` (perceptibly smooth, still useful) |
| `g_aim_hotkey` | (no default) | Right-mouse-button (industry convention for "aim assist") |
| `g_aim_fov` | `1000.0` (whole screen) | `60.0` (focused, sane starting point) |
| `g_esp_max_distance` | `0.0` (draws nothing) | `200.0` (covers most engagements) |
| `g_radar_radius` | `40.0` (too small to read) | `90.0` (readable on 1080p+ displays) |

The pre-ship hygiene check (`tools/pre-ship-check.sh`) does NOT catch bad defaults — they look like normal values to grep. Reviewers must consciously test the fresh-config experience: delete your saved config, restart the script, verify it does something visible without any user tuning.

**Why:** Defaults are the product. A user who has to tune 20 widgets before the feature works will conclude the feature doesn't work. The two minutes you spend picking defaults that work for a first-time user pay back in every install.

---

## Hotkey Conventions

**Don't bind features to letter keys the game uses (WASD, R, E, F, Q). Provide a `section_keybind` widget for every hotkey — hardcoded hotkeys are rule-#11 violations.**

Safe default hotkeys, ordered by convention:

| Action | Conventional default |
|---|---|
| Toggle aim assist (hold) | Right Mouse Button (`VK_RBUTTON`) — industry standard |
| Toggle aim assist (toggle) | `F1` or `Mouse5` (`XBUTTON2`) |
| Open / close menu | `Insert` (PCX default) or `End` |
| Toggle ESP | `F2` |
| Toggle radar | `F3` |
| Misc feature toggles | `F4` – `F11` |
| Panic / hide all overlays | `End` or `\` |
| Reload sigs | `Home` (rare, RE-only utility) |
| Snapshot for debugging | `Pause` |

What to NEVER use:
- `WASD` — movement keys
- `Q`, `E`, `R`, `F` — typical ability / interact keys
- `Space`, `Shift`, `Ctrl`, `Alt` — modifier keys the game routes
- `1`–`0` — weapon swap / hotbar
- `Escape` — game-menu trigger
- `~` — chat or console
- Mouse4 / Mouse5 — generally OK, but check; some games bind these

Every hotkey is exposed as a `section_keybind` widget so the user can rebind:

```cpp
// RIGHT — hotkey is configurable
int64 g_esp_hotkey = vk::f2;
section_keybind(sec, "ESP toggle", g_esp_hotkey);

void on_update(int64 data) {
    if (key_fired(g_esp_hotkey)) {
        g_esp_enabled = !g_esp_enabled;
    }
}

// WRONG — hardcoded hotkey, user can't rebind
void on_update(int64 data) {
    if (key_fired(vk::f2)) {
        g_esp_enabled = !g_esp_enabled;
    }
}
```

`key_fired` is edge-triggered (true once per press); `key_down` is level-triggered (true while held). Toggles use fired; hold-to-activate uses down.
**Why:** Hotkey conflicts kill scripts. The user reports "the script doesn't work" — actually the script's `F` hotkey collides with the game's interact key, and pressing it both triggers the script and opens a door. Configurable hotkeys eliminate the entire class of report.

---

## Color Discipline

**Every drawable color is GUI-tunable (per rule #11). The discipline: a small palette per feature (FG / BG / accent) rather than per-pixel colors.**

A feature with 12 distinct hardcoded colors is one the user can't recolor for high-contrast, colorblind-friendly, or stream-friendly use. A feature with 3-4 tunable palette slots is one the user can adapt.

```cpp
// RIGHT — small palette, all tunable
color g_esp_friendly = color(60, 170, 255, 255);
color g_esp_enemy    = color(255, 60, 60, 255);
color g_esp_text     = color(255, 255, 255, 255);
color g_esp_outline  = color(0, 0, 0, 180);

int64 sec = create_section("ESP");
section_color_picker(sec, "Friendly",  g_esp_friendly);
section_color_picker(sec, "Enemy",     g_esp_enemy);
section_color_picker(sec, "Text",      g_esp_text);
section_color_picker(sec, "Outline",   g_esp_outline);

// In render — pull from the palette, never construct ad-hoc colors:
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        color box = g_cache[i].friendly ? g_esp_friendly : g_esp_enemy;
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  box, 1.5, 0.0, 15);
    }
}

// WRONG — hardcoded per-call colors
void on_render(int64 data) {
    for (int32 i = 0; i < g_count; i++) {
        draw_rect(g_cache[i].screen_pos, g_cache[i].screen_size,
                  color(255, 0, 0, 255),   // hardcoded red
                  1.5, 0.0, 15);
    }
}
```

Community conventions for color roles:

| Role | Conventional color |
|---|---|
| Friendly / teammate | Blue (`60, 170, 255`) or Green (`60, 220, 100`) |
| Enemy | Red (`255, 60, 60`) or Yellow (`255, 200, 50`) |
| Neutral / NPC / object | Gray (`180, 180, 180`) |
| Important / priority target | Magenta (`255, 60, 255`) or Bright Orange (`255, 140, 0`) |
| Hostile NPC (distinct from enemy player) | Dark red (`140, 30, 30`) or Crimson |
| Loot / pickup | Yellow (`255, 220, 80`) or Gold |

These are conventions, not laws — users will adjust. The point is to ship defaults that match what most users expect from prior cheats / games, so the first impression makes visual sense.

**Why:** Colors are accessibility. ~8% of male users have some form of red-green color blindness; ship colors they can tell apart, and let users override them if your defaults don't work for them.

---

## State Visibility

**A small label at the bottom of each section showing the runtime state. When users report "the script isn't working," the first thing they read is the state label.**

The state label closes the support loop before it opens. Without it, a user with a broken script reaches for Discord; with it, the user reads "0 entities (sig scan failed)" and knows the problem is the sig, not the feature.

```cpp
// In render — build status from cached state, update each frame
void on_render(int64 data) {
    // ... drawing ...

    // Status label — built from cached state
    string status;
    if (!g_proc.alive()) {
        status = "process not attached";
    } else if (g_entity_list == 0) {
        status = "sig scan failed (entity_list)";
    } else if (g_ent_count == 0) {
        status = "0 entities (in menu?)";
    } else {
        status = format("{d} entities ({d} friendly, {d} enemy)",
                        g_ent_count, g_ent_friendly_count, g_ent_enemy_count);
    }
    section_label(sec, status);
}
```

The status should:
- Always be visible (don't gate on `g_enabled` — the user wants status even when the feature is off)
- Use plain English (no internal error codes)
- Differentiate the common failure modes from "working fine"
- Include a count or sample value when the feature is working (proves it)

For features that have multiple status dimensions (aimbot: "no target / target locked: enemy_42 / smoothing: 8 frames"), one label is enough — `format` them together.

**Why:** The status label is the support burden's lightning rod. A user who can read the status doesn't ask in Discord; a user who can't, does.

---

## Conditional Widgets

**If widget B only makes sense when widget A is enabled, hide or gray out B when A is off.**

PCX's GUI API may or may not expose disable-state styling natively — check `docs/perception/gui-api.md` for the available widget states. If a disable-state is available, use it; if not, fall back to *conditionally creating* the dependent widgets, or document the dependency with a comment.

```cpp
// PATTERN 1 — if PCX supports a `section_*_disabled` variant or visibility flag,
// use it (check docs):
section_checkbox(sec, "Aim assist",  g_aim_enabled);
// Hypothetical: section_set_enabled(g_aim_smoothing_widget, g_aim_enabled);

// PATTERN 2 — fall-back: only create the dependent widget when the
// parent is enabled, on a per-frame basis. PCX GUI API permitting,
// recreate-per-frame is fine; if not, fall back to PATTERN 3.

// PATTERN 3 — universal fall-back: keep the widgets always created,
// but make the dependency explicit in the label and ignore the value
// at runtime when the parent is off:
section_checkbox(sec, "Aim assist", g_aim_enabled);
section_slider_float(sec, "Smoothing (needs Aim assist)",
                     g_aim_smoothing, 0.0, 15.0);
// In on_update: read g_aim_smoothing only inside `if (g_aim_enabled)`.
```

The labeled-dependency pattern (#3) is uglier than gray-out but always works. Use the prettier patterns when PCX exposes them; document with a `// requires: g_aim_enabled` comment either way.

**Why:** A user enabling smoothing without realizing aim assist is off, then concluding "the script is broken," is the exact kind of confused-customer report a 12-character label change prevents.

---

## Don't Ship a Debug Panel by Default

**A separate "Debug" section with profiler readouts and address dumps is great for development; hide or remove for release. The pre-ship checklist catches this.**

```cpp
// During development
int64 sec_debug = create_section("Debug");
section_label(sec_debug, format("entity_list: 0x{x}", g_entity_list));
section_label(sec_debug, format("local_player: 0x{x}", g_local_player));
section_label(sec_debug, format("entity count: {d}", g_ent_count));
section_label(sec_debug, format("update_us: {d}", g_avg_update_us));
section_label(sec_debug, format("render_us: {d}", g_avg_render_us));

// Before shipping — either remove the section entirely, or gate it
// behind a build flag / runtime "Show debug" checkbox in Misc.
#if DEBUG
    int64 sec_debug = create_section("Debug");
    // ... debug widgets ...
#endif
```

(PCX's preprocessor supports `#if`/`#ifdef`; see `docs/enma/lang-pre-processor.md`.)

The recipient of a shipped script does not need to see your internal address layout, your profiler bucket timings, or your sig-resolution status. Worse, debug info exposes the script's internals to anyone watching over the recipient's shoulder, which is bad for both privacy and competitive dynamics.

When shipping with a "Show debug" toggle (the gentler approach), default it off, and document in the README that flipping it on reveals diagnostic info useful only for support tickets.

**Why:** Debug surfaces are for the author, not the user. Shipping them on by default is leaking implementation; shipping them gated off (with documentation) is offering a support feature without imposing it.

---

## Persistence (Cross-Reference)

The GUI state must be persisted across script reloads — the user doesn't want to retune sliders every time. See `knowledge/script-organization-patterns.md` section "Config persistence pattern" for the JSON-to-disk pattern, and `.claude/skills/script-bundler/SKILL.md` for when to save (on each widget change, on a debounced timer, or on a save hotkey).

The relevant `fs_*` and `json_*` APIs are in `docs/perception/file-api.md` and `docs/enma/addon-json.md`. The summary: read on `main()` startup, write on a save hotkey or a debounced timer.

---

## Worked Example: A Well-Laid-Out ESP Section

```cpp
import "vec";
import "color";

// ── Config (GUI-bound; persisted to disk by main()) ──
bool   g_esp_enabled       = true;            // default ON (rule: defaults that work)
int32  g_esp_hotkey        = 0x71;            // VK_F2 toggle
int32  g_esp_mode          = 0;               // 0=box, 1=skeleton, 2=both
float64 g_esp_max_dist     = 200.0;
int32  g_esp_thickness     = 2;
bool   g_esp_show_distance = true;
color  g_esp_color_friendly = color(60, 170, 255, 255);   // blue convention
color  g_esp_color_enemy    = color(255, 60, 60, 255);    // red convention
color  g_esp_color_outline  = color(0, 0, 0, 180);

// ── Runtime state (status label reads these) ──
int32 g_esp_count_drawn    = 0;
int32 g_esp_count_friendly = 0;
int32 g_esp_count_enemy    = 0;
string g_esp_status_text   = "initializing";

int64 setup_esp_gui() {
    int64 sec = create_section("ESP");

    // 1. Master toggle (top)
    section_checkbox(sec, "Show ESP", g_esp_enabled);
    // 2. Hotkey
    section_keybind(sec, "Toggle hotkey", g_esp_hotkey);
    // 3. Primary tuning
    section_combo(sec, "Mode", g_esp_mode, "Box,Skeleton,Both");
    // 4. Secondary tunings (useful ranges, not possible ranges)
    section_slider_float(sec, "Max distance (m)", g_esp_max_dist, 0.0, 500.0);
    section_slider_int(sec, "Line thickness (px)", g_esp_thickness, 1, 5);
    section_checkbox(sec, "Show distance label", g_esp_show_distance);
    // 5. Color pickers (palette, not per-pixel)
    section_color_picker(sec, "Friendly", g_esp_color_friendly);
    section_color_picker(sec, "Enemy",    g_esp_color_enemy);
    section_color_picker(sec, "Outline",  g_esp_color_outline);
    // 6. Separator
    section_separator(sec);
    // 7. Status label (always-visible feedback)
    section_label(sec, g_esp_status_text);

    return sec;
}
```

This is 12 widgets in 7 logical roles. A user scanning this section knows in seconds: "ESP is on (toggle), F2 toggles it (keybind), it's drawing boxes (mode), out to 200m (distance), in blue/red (palette), and right now is drawing 12 entities (status)."

---

## Anti-Patterns

Flat list — each is a real failure mode that ships in scripts and gets reported:

- **All features in one section.** Sidebar becomes a wall of widgets; users can't collapse-and-skip.
- **Hotkeys hardcoded.** User can't rebind, hotkey collides with a game key, support ticket follows.
- **Slider ranges 0..1000 for 0..15 problems.** Slider is unusable for the actual range.
- **No master toggle.** User can't disable the feature without quitting the script.
- **`color()` / `vec2()` globals at file scope.** Per-frame construction rule (#7) violated; harder to recolor.
- **Labels "foo" / "bar" / "new feature".** Self-evident at write time, opaque a week later.
- **Defaults of 0 / false on user-facing toggles.** Script appears broken on fresh install.
- **No status label.** Every support ticket reads "the script isn't working" with no diagnostic info.
- **Debug section always visible in release.** Leaks internals; clutters the UX.
- **All widgets enabled regardless of dependencies.** User enables smoothing without aim assist on, concludes script is broken.
- **No section separators.** Every section looks the same; visual fatigue.
- **Tooltips encoded into labels.** "Smoothing (higher = smoother, lower = snappier, default 8)" doesn't fit; use a separator + label below instead, or a dedicated `Help` section.

---

## Cross-References

- `docs/perception/gui-api.md` — the authoritative widget API for your PCX version
- `templates/overlay-basic.em` — a working small-overlay GUI
- `templates/full-project/` — the multi-feature project scaffold
- `knowledge/common-patterns.md` — Enma code patterns that consume the widget values
- `knowledge/script-organization-patterns.md` — the persistence pattern, the menu-vs-feature split
- `.claude/skills/game-cheat-guidelines/SKILL.md` rules #6 (one feature per file) and #11 (GUI for every tunable)
- `.claude/skills/script-bundler/SKILL.md` — the pre-ship hygiene checklist that includes "sensible GUI defaults"
- `.claude/skills/ai-pair-programming/SKILL.md` — technique #6 for diff-reviewing AI-generated GUI code

---

## Source: `knowledge/kernel-re-tools.md`

# Kernel-Level Reverse Engineering Tools

Tools for reversing kernel drivers, analyzing anti-cheat systems, and inspecting kernel state. Organized by workflow stage.

> **Scope:** Authorized security research only. See `skill://authorized-security-research` before pointing any tool at a live system. AC driver analysis should happen in an isolated VM, never on a production box.

---

## Static Analysis (Driver Binaries)

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **IDA Pro** | Disassembler + decompiler. The standard for driver reversing — FLIRT sigs for ntoskrnl, WDK type libraries, Hex-Rays decompiler. | Win/Linux/macOS | `idalib` MCP wired in this toolkit (`mcp/binary-analysis-setup.md`) |
| **Ghidra** | Free decompiler. Supports PE drivers, PDB loading, WDK headers via GDT. Slower than IDA but scriptable (Java/Python). | Cross-platform | Ghidra MCP available (`ghidra` server) |
| **radare2 / rizin** | CLI disassembler. Fast triage: `r2 -AA driver.sys` → `afl` (function list), `pdf @ sym.DriverEntry` (disasm entry). | Cross-platform | `radare2` MCP wired in this toolkit |
| **Binary Ninja** | Interactive disassembler with IL (BNIL). Good for automated analysis via Python API. | Win/Linux/macOS | — |
| **CFF Explorer** | PE header viewer. Quick check: driver subsystem (NATIVE), imports, sections, certificate chain. | Windows | — |
| **PE-bear** | PE parser. Shows imports, relocations, resources, overlay. | Cross-platform | — |

## Kernel Debugging

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **WinDbg** | Microsoft kernel debugger. The only way to single-step kernel code, inspect EPROCESS/ETHREAD, walk callback arrays. Requires a debug target (VM or serial/net). | Windows | Essential for AC analysis |
| **WinDbg Preview** | Modern UI wrapper for the same engine. Same commands, better UX. | Windows | From Microsoft Store |
| **VirtualKD-Redux** | Patches the VM's `kdcom.dll` to use a fast pipe instead of serial — 10–40× faster kernel debugging in VMware/VirtualBox. | Windows (host+guest) | Use with WinDbg |
| **KD (kd.exe)** | Console-mode kernel debugger. Same engine as WinDbg, scriptable. | Windows | `kd -k net:port=50000,key=...` |
| **HyperDbg** | Hypervisor-level debugger. Sits *below* the OS — invisible to kernel anti-debug. Supports stealth breakpoints, EPT hooks, syscall interception. | Windows | Runs as a custom hypervisor; the AC cannot detect it via standard means |
| **QEMU + GDB** | GDB stub for kernel debugging Linux/Windows guests. `-s -S` flags expose a GDB server on port 1234. | Cross-platform | `target remote :1234` in GDB |

## Memory Forensics (Offline Analysis)

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **Volatility 3** | Memory forensics framework. Analyze memory dumps: driver lists, callback arrays, SSDT, IDT, process trees, handle tables. | Cross-platform (Python) | `vol -f dump.raw windows.driverscan`, `windows.callbacks` |
| **Rekall** | Alternative memory forensics. Similar to Volatility, different plugin architecture. | Cross-platform (Python) | Less actively maintained |
| **WinPmem** | Memory acquisition driver. Dumps physical RAM to a file for offline analysis. | Windows | Requires admin; the AC may detect the acquisition driver |
| **PCILeech** | DMA-based memory acquisition via FPGA or Thunderbolt. Reads physical memory without software on the target — invisible to kernel ACs. | Hardware + host | Requires FPGA board (e.g., Screamer, LambdaConcept) or Thunderbolt access |
| **MemProcFS** | Virtual file system for physical memory analysis. Mount a memory dump (or live DMA feed) as a filesystem and browse processes, modules, registry. | Windows/Linux | Works with PCILeech for live analysis |

## Runtime Monitoring

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **Process Monitor** | Real-time file, registry, process, network, and thread activity. Filter by `driver.sys` to see what the AC touches at load time. | Windows | Sysinternals |
| **Process Explorer** | Enhanced task manager. Shows DLLs, handles, GPU, threads. Check what the AC injects and what handles it opens. | Windows | Sysinternals |
| **IRPMon** | Intercepts IRPs (I/O Request Packets) to/from drivers. Use to capture IOCTL traffic between AC user-mode and kernel components. | Windows | Open source; AC may detect it |
| **API Monitor** | Hooks Win32/NT API calls. Capture `DeviceIoControl` calls, `NtQuerySystemInformation`, `NtOpenProcess` from the AC user-mode module. | Windows | Heavy but detailed |
| **DebugView++** | Captures `DbgPrint` / `OutputDebugString` output from drivers and user-mode. | Windows | Sysinternals successor |
| **OSR Device Monitor** | Legacy IOCTL monitor. Simpler than IRPMon for basic IOCTL capture. | Windows | — |

## Driver Development / Testing

| Tool | What It Does | Platform | Notes |
|------|-------------|----------|-------|
| **WDK (Windows Driver Kit)** | Headers, libs, build tools for kernel development. Essential for understanding AC driver structures — the headers define every callback type, IRP structure, and IOCTL macro. | Windows | Free from Microsoft |
| **OSR Driver Loader** | Loads unsigned drivers for testing (requires test-signing mode). | Windows | — |
| **kdmapper** | Manual-maps a driver into kernel without loading via SCM — no entry in PsLoadedModuleList. Educational: understand how cheat drivers avoid detection. | Windows | Research only |
| **EfiGuard** | Disables DSE (Driver Signature Enforcement) and PatchGuard from the UEFI bootloader. Research tool for understanding boot-time security. | UEFI | Research only — pre-boot |

## Perception.cx Integration

| Tool | Surface | What It Does |
|------|---------|-------------|
| `system/list_drivers` | MCP | Enumerate loaded kernel modules (gated: `kernel_rw_access`) |
| `get_eprocess` | `proc_t` (Enma/AS) | Get target's EPROCESS kernel address (gated: `kernel_rw_access`) |
| `ru64` / `ru32` / `read_struct` (kernel range) | `proc_t` (Enma/AS) | Read kernel memory when `kernel_rw_access` is granted |
| `find_code_pattern` | `proc_t` (Enma/AS) | Pattern-scan driver `.text` sections |
| `struct_dump` | Perception IDE AI tool | Heuristically dump + classify a driver data structure at an address |
| `process/disassemble` | MCP | Disassemble driver code at kernel addresses |
| `process/analyze_vtable` | MCP | Walk vtables in kernel objects |
| `process/find_xrefs` | MCP | Find code references into driver `.text` |

## Recommended Analysis Environment

```
┌─────────────────────────────────────┐
│  Host (Linux/macOS)                 │
│  ├── IDA Pro / Ghidra / r2          │  ← Static analysis of driver binaries
│  ├── Volatility 3                   │  ← Offline analysis of VM snapshots
│  └── WinDbg via network KD          │  ← Kernel debug the VM
│                                     │
│  ┌──────────────────────────────┐   │
│  │  VM (Windows — test-signing) │   │
│  │  ├── Game + anti-cheat       │   │  ← Target
│  │  ├── Process Monitor         │   │  ← Runtime monitoring
│  │  ├── IRPMon                  │   │  ← IOCTL capture
│  │  └── Debug serial/net to host│   │  ← KD pipe to host WinDbg
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Key rule:** Never analyze from the same OS instance the AC is running on. The AC monitors for debugger artifacts, analysis tools, and VM-escape attempts. Use a VM with snapshots — snapshot before installing the AC, so you can revert cleanly.

---

## Source: `knowledge/network-protocol-re.md`

# Network Protocol Reverse Engineering Reference

How to reverse-engineer a game's network protocol — capture, dissect, identify message boundaries, decode payloads. The defensive / educational half of network RE; pairs with the engine-RE references for the on-disk and in-memory sides. Useful for understanding what a game tells the server (anti-cheat telemetry shape, replay format design, server-message bus structure), for protocol documentation, and for legitimate research on private/community-run servers.

> **Scope:** Educational reference for authorized targets only. Network RE against live commercial servers may violate the game's Terms of Service or local computer-misuse statutes; see `skill://authorized-security-research` before pointing tooling at any non-owned endpoint. Private servers, your own development environment, packet captures from your own machine, and protocol research published by the game's own developers are the normal authorized scope.

---

## What This File Covers

- The packet-capture toolchain (Wireshark, tshark, mitmproxy, eBPF-tracing alternatives) and when to use which
- Identifying message-boundary patterns in TCP / UDP / WebSocket / QUIC game protocols
- Common encoding schemes games use (length-prefixed, type-tagged, varint-encoded, protobuf-shaped, FlatBuffers-shaped, custom-shaped)
- Encryption recognition — what TLS / DTLS / custom XOR / custom block-cipher looks like at the wire level
- Cross-referencing wire data to in-memory structures (the "this packet field is the same as the entity struct's m_iHealth" link)
- What to do when the protocol is over QUIC / HTTP3 (most modern AAA titles have moved here)

What this file does NOT cover:

- Server-side server-emulator authoring (out of scope; see project-specific server-emulator communities)
- Live MITM against production servers (not legal in most jurisdictions; not described here)
- Protocol cracking for the purpose of bypassing server-side validation (an exploit category outside this toolkit's scope)

---

## Capture Toolchain

Pick the tool by what you're capturing:

| Tool | Best for | Notes |
|---|---|---|
| **Wireshark** (GUI) | Interactive dissection, custom Lua dissectors, named TCP/UDP streams | The default. Filter syntax (`tcp.port == 27015 && data.len > 8`) is the productive surface. |
| **tshark** (CLI) | Scripted captures, batch processing, pcap-to-text pipelines | Same engine as Wireshark; CLI lets you grep raw payload bytes. |
| **mitmproxy / mitmweb** | HTTP / HTTPS / WebSocket traffic (with cert injection) | Useful for the increasing number of games that use HTTPS endpoints for matchmaking / inventory / telemetry. Requires the game to trust the mitmproxy CA. |
| **dumpcap** (Wireshark backend) | Long-running unattended captures, headless servers | Lighter-weight than full Wireshark; saves to `.pcap` / `.pcapng`. |
| **tcpdump** | Quick captures on Linux / macOS; minimal install | Older but ubiquitous. Output goes to `.pcap` for offline analysis. |
| **bpftrace / eBPF** | In-kernel filtering of high-volume traffic, custom sampling | Modern alternative when packet rates exceed userspace capture. |
| **PCAP-NG with comment annotations** | Persisted analysis context | Annotate packets with notes; survives reopening. |

For QUIC / HTTP3 (the increasing default for modern AAA titles): regular `.pcap` capture works at the IP/UDP level, but you need the connection's TLS keys to see inside. Browsers can dump these to `SSLKEYLOGFILE`; games typically don't. Without the keys, you see encrypted blobs and per-packet timing only.

The recommended starter setup: Wireshark with a Lua dissector for the game (described below), capturing the game's process traffic via the right interface (loopback if you're running a local server; the LAN interface if you're inspecting traffic to a remote server).

---

## Identifying Message Boundaries

Game protocols universally have a structure on top of TCP/UDP for delimiting application-level messages. Identifying that structure is step one of any dissection.

### TCP-based protocols

TCP is a byte stream; the game has to delimit its own messages on top. The three common patterns:

**Length-prefixed** — the most common modern pattern. Each message starts with N bytes encoding the rest of the message's length:

```
[ 2-byte length ] [ N-byte payload ]
or
[ 4-byte length ] [ N-byte payload ]
or
[ varint length ] [ N-byte payload ]
```

Recognize by: opening a Wireshark stream, looking at the first 2-4 bytes of each `tcp.stream` flow; the small integer value (matching the rest of the payload's byte count) is the length field.

**Type-tagged** — message starts with a type byte, then a per-type fixed or known-shape payload:

```
[ 1-byte type ] [ type-specific payload ]
```

Recognize by: the same byte value (e.g. `0x07`) appearing at regular intervals; the bytes following it have a stable shape for that type.

**Self-describing (rare in games, common in protobuf RPC)** — each message carries its own wire format hints:

```
[ varint tag ] [ varint length ] [ payload ] [ varint tag ] [ varint length ] [ payload ] ...
```

Recognize by: byte values 0x08-0x7F appearing as type tags, with varint length following.

### UDP-based protocols

UDP datagrams are inherently message-bounded — one datagram = one application message (or a fragment, if the game does its own fragmentation). The patterns:

- **Sequence-numbered** — header carries sequence + ack info for reliability layering. Quake/Source-engine style.
- **Type-prefixed** — same as TCP type-tagged but at datagram start.
- **Encrypted-blob** — datagram is opaque; key is exchanged during the initial handshake (often DTLS or a custom equivalent).

### Worked example: a length-prefixed TCP protocol

Suppose Wireshark shows you a TCP stream with payload starting:

```
0c 00 07 00 14 00 41 6c 69 63 65 00
0e 00 09 00 26 00 42 6f 62 73 31 32 33 00
05 00 12 00
```

Pattern recognition:
- Byte 0-1: `0c 00` = 12 (little-endian uint16) — and the payload after the length is exactly 12 bytes (`07 00 14 00 41 6c 69 63 65 00` is 10, plus the next 2 bytes... wait, count: 0c 00 means 12 bytes follow). Re-checking: 12 bytes after position 2 = positions 2..13. That includes `07 00 14 00 41 6c 69 63 65 00` (10 bytes) + 2 more. Yes, 12.
- Byte 14-15: `0e 00` = 14 (uint16 LE). 14 bytes follow.
- Byte 30-31: `05 00` = 5. 5 bytes follow.

The protocol shape:
```
struct Message {
    uint16_t length;          // little-endian
    uint8_t  type;            // example: 0x07 = login, 0x12 = heartbeat
    uint8_t  reserved;        // padding or flags
    uint16_t subtype_or_seq;  // 0x0014 / 0x0009 / etc
    // ... type-specific payload, ending with a null-terminated string in cases
}
```

Once you've identified the boundary mechanism, you can write a Wireshark dissector that splits the stream correctly.

---

## Wireshark Lua Dissector — the Productive Surface

Wireshark's Lua dissector API turns "raw byte stream" into "annotated tree of named fields" in the packet view. For any game you'll spend more than a few sessions reversing, the dissector is worth writing.

Minimal example for the length-prefixed protocol above:

```lua
-- mygame.lua — save in ~/.config/wireshark/plugins/ (Linux/macOS)
--                          or %APPDATA%\Wireshark\plugins\ (Windows)

local mygame_proto = Proto("mygame", "MyGame Protocol")

local f_length  = ProtoField.uint16("mygame.length",  "Length",  base.DEC)
local f_type    = ProtoField.uint8 ("mygame.type",    "Type",    base.HEX)
local f_subtype = ProtoField.uint16("mygame.subtype", "Subtype", base.HEX)
local f_payload = ProtoField.bytes ("mygame.payload", "Payload")

mygame_proto.fields = { f_length, f_type, f_subtype, f_payload }

function mygame_proto.dissector(tvbuf, pktinfo, root)
    pktinfo.cols.protocol = "MyGame"
    local subtree = root:add(mygame_proto, tvbuf())

    subtree:add_le(f_length,  tvbuf(0, 2))
    subtree:add   (f_type,    tvbuf(2, 1))
    subtree:add_le(f_subtype, tvbuf(4, 2))
    subtree:add   (f_payload, tvbuf(6))

    -- Optional: per-type sub-dissection
    local t = tvbuf(2, 1):uint()
    if t == 0x07 then
        pktinfo.cols.info = "LOGIN  " .. tvbuf(6):string()
    elseif t == 0x12 then
        pktinfo.cols.info = "HEARTBEAT"
    end
end

-- Register on the game's TCP port (replace with the actual port)
DissectorTable.get("tcp.port"):add(27015, mygame_proto)
```

Reload Wireshark; reopen the pcap; messages now show as MyGame instead of raw bytes. Iteratively add types as you identify them.

The dissector becomes the documentation of the protocol — sharing the `.lua` file is sharing the spec.

---

## Common Encoding Schemes

Game protocols converge on a handful of payload-encoding strategies:

### Plain-old struct dump

Fields written in declaration order, native byte order (usually little-endian on x86 / x64 games). The simplest case; recognize by per-field alignment matching a known struct.

### Length-prefixed strings

A length byte (or short) followed by N characters. Sometimes UTF-8, sometimes UTF-16LE (Windows-influenced engines), sometimes the game's own encoding for known character set restrictions (e.g. ASCII-only for usernames).

### Varint encoding (protobuf-style)

Each byte's high bit indicates "more to follow"; the low 7 bits accumulate into the integer. Recognize: bytes in range `0x80-0xFF` followed eventually by a byte `< 0x80`. Used by Protocol Buffers, FlatBuffers' varint helpers, and many custom encodings inspired by protobuf.

### Protobuf-shaped payloads

If the game uses Protocol Buffers (common for Google-stack games and many modern titles), the wire format is well-documented (https://protobuf.dev/programming-guides/encoding/). Per field: varint tag (combining field number and wire type), then payload (varint / fixed64 / length-delimited / start-group / end-group / fixed32). With the `.proto` schema (sometimes leaked, sometimes inferrable), the data decodes cleanly.

Even without the schema, you can identify protobuf by the tag byte pattern: low 3 bits encode wire type (0-5), upper 5+ bits the field number. Field 1, wire-type 0 (varint) = tag byte `0x08`. Field 1, length-delimited = `0x0A`. Field 2, length-delimited = `0x12`. Lots of `0x08`, `0x0A`, `0x10`, `0x12` etc. at message starts = protobuf.

### FlatBuffers-shaped payloads

Random-access binary format from Google. Recognize by the file/message header carrying a root-table offset, vtable indirection inside tables. More complex to decode without the schema; less common in games than protobuf.

### Custom-shaped — bit-packed fields

Some performance-sensitive game protocols (especially older Quake-derived ones) pack fields into bits to save bandwidth. Recognize by: byte values that don't decode cleanly as bytes; field boundaries that don't align to byte boundaries. Requires bit-level analysis.

### Compressed payloads

Larger payloads are often compressed before the wire — zlib / LZ4 / Zstd / LZF / Snappy. Recognize by: payload starting with a known magic number (`78 9C` for zlib default level, `78 DA` for max, `04 22 4D 18` for LZ4 frame, `28 B5 2F FD` for Zstd) or by entropy that's near uniform (compressed data looks like noise).

Decompress before dissecting the inner payload.

---

## Encryption Recognition

Games are increasingly TLS-wrapped, but not all. Identifying whether (and how) a stream is encrypted is step one of any deeper analysis.

### TLS / SSL on TCP

Recognize by:
- Stream starts with the TLS handshake (`16 03 01` for TLS 1.0 ClientHello, `16 03 03` for TLS 1.2)
- Wireshark identifies it as `tls` protocol automatically
- Application data records have header `17 03 03 <len-16>`

To see inside: you need the session keys. Browsers and many tools dump these to a file pointed at by `SSLKEYLOGFILE`; games rarely do. Without keys, you see encrypted blobs only.

### DTLS on UDP

The UDP equivalent of TLS. Recognize by similar handshake bytes at datagram start (`16 fe ff` ClientHello, etc.) and the `dtls` protocol detection in Wireshark.

### Custom XOR / stream cipher

Older / simpler games sometimes apply a per-byte XOR with a static or short-rotating key. Recognize by:
- Entropy is higher than plain text but lower than CSPRNG output (encrypted "looks like noise but not quite as noisy as TLS")
- Same byte positions across many messages have a repeating value-distribution (a fixed key betrays itself)
- The XOR key sometimes leaks via the game binary (search `tools/dump-strings-xor.py` for the key recovery angle on the on-disk side)

### Custom block cipher (AES / similar)

The game may apply AES-CBC or AES-GCM with a key negotiated in a custom handshake. Recognize by: 16-byte-aligned payload chunks (block boundary), high entropy throughout, deterministic-looking IV/nonce field at message start.

Without the key, indistinguishable from random; recover the key by reversing the game's handshake code on the binary side.

### Compression + obfuscation combo

Some games compress then XOR (or vice versa). Decompress first if you can identify the compression magic; XOR-recover then.

---

## Cross-Referencing Wire Data to In-Memory Structures

The synthesis step: wire-format field X corresponds to in-memory struct field Y. Once you have this, the game's protocol becomes a window into the game's state.

The workflow:

1. **Identify a known field in memory.** E.g. `m_iHealth` at offset 0x40 of the entity struct, value 100, observed via PCX's `mcp:struct_dump`.
2. **Take an in-game action that changes that field.** Take damage; health drops to 87.
3. **Capture the network traffic around the action.** Wireshark or tshark with a tight time filter.
4. **Find the byte pattern that changed correspondingly.** A 4-byte field that was `64 00 00 00` (100 LE) in a pre-action packet, now `57 00 00 00` (87 LE) in a post-action packet.
5. **Confirm with a second action.** Take more damage; verify the wire field tracks.

Once you've mapped one field, the same packet's neighboring bytes are candidates for other fields. Build the mapping incrementally; document in the dissector.

The cross-reference is bidirectional:
- Wire → memory: "this server-sent field updates the in-memory health field"
- Memory → wire: "this in-memory field is sent at this byte position in this message type"

Both directions are useful: the first for understanding what the server tells the client; the second for understanding what the client tells the server (which is the more interesting half for anti-cheat-telemetry research and replay-format work).

---

## When the Protocol Is QUIC / HTTP3

Increasing fraction of modern AAA titles use QUIC (HTTP/3) for matchmaking, telemetry, and sometimes game traffic. QUIC is UDP-based and encrypted by default; capture without keys shows you UDP datagrams with QUIC-protocol headers but no payload visibility.

Options:

- **Connection-side key dump.** If you control either endpoint (your own game client running in a dev environment, or a private-server target you own), tools like `keylogger.so` or `SSLKEYLOGFILE` (where supported by the QUIC library) dump the session keys. Wireshark + the keylog file decrypts the QUIC stream.
- **Process-side hooking.** Hook the game's QUIC library (msquic, quiche, ngtcp2, the game's own custom QUIC implementation) before encryption to capture cleartext. This is much more invasive (DLL injection or LD_PRELOAD on the client) and only legal on systems you own.
- **Endpoint observation, not wire observation.** Use the game's own logs / debug builds / leaked SDK to see what *would* be sent at the application layer, even without decrypting the wire. Often easier than full QUIC decryption.

QUIC's encryption-by-default has made wire-level RE materially harder than it was during the TCP-with-optional-TLS era; expect to pair wire analysis with binary-side analysis to a much greater extent for modern titles.

---

## Replay Files — the Persisted Cousin

Many games persist game state in a `.dem` / `.replay` / `.rec` file. The replay format is often a *recording of the network protocol* — the server-to-client message stream, written to disk verbatim plus a header. If so, decoding the replay file is the same problem as decoding the network protocol.

For Source-engine games, `.dem` files are well-documented community-side; for modern titles, the format is typically reverse-engineered per-game by community replay-parser projects.

The dissector you wrote for the network protocol is usually directly reusable for the replay file — point it at the `.dem` instead of a `.pcap`. This makes replay-based RE much cheaper than live capture (no game required, no server required, deterministic for repeated analysis).

---

## Cross-References

- `skill://authorized-security-research` — what's in scope for any network-side analysis
- `knowledge/anti-cheat-architecture.md` — the AC side of network telemetry
- `knowledge/kernel-re-tools.md` — the binary-side counterpart for understanding the game's network code
- `knowledge/engine-cryengine.md` / `engine-frostbite.md` / etc. — engine-specific network architecture notes
- `tools/dump-strings-xor.py` — recovers XOR keys from a game binary (the on-disk side of custom-XOR-encrypted protocols)
- `tools/identify-protector.py` — flags binaries with anti-tamper layers that often also wrap the network code
- `.claude/skills/re-evidence-log` — the per-binary evidence-citation discipline applies to wire-format field mappings the same way it applies to in-memory ones
- Wireshark docs — https://www.wireshark.org/docs/ (the comprehensive reference for the toolchain)

---

## Source: `knowledge/obfuscation-taxonomy.md`

# Obfuscation & Protector Taxonomy

Architecture, VM internals, protection layers, and known weaknesses for every major commercial and open-source binary protector. Read this before starting deobfuscation — it tells you what you're fighting and where each protector is weakest.

---

## Commercial Protectors

### Themida / WinLicense (Oreans Technologies)

| Property | Detail |
|----------|--------|
| **Publisher** | Oreans Technologies |
| **Products** | Themida (code protection), WinLicense (code + licensing), Code Virtualizer (VM-only) |
| **Platforms** | Windows x86/x64, .NET |
| **Protection layers** | Anti-debug, anti-dump, code mutation, import redirection, resource encryption, VM virtualization |
| **VM architectures** | FISH, TIGER, DOLPHIN, EAGLE, SHARK (ascending strength) |

**VM Architecture:**

Each Themida VM is a register-based bytecode interpreter:

| Component | Implementation |
|-----------|---------------|
| **Dispatcher** | Computed goto: `jmp [reg*8 + handler_table]` |
| **Virtual PC** | Register (typically `RBX` or `R12`) pointing into bytecode stream |
| **Virtual stack** | Real stack reused, or dedicated memory region |
| **Virtual registers** | 8-16 virtual registers mapped to a stack-frame struct |
| **Bytecode** | Stored in `.themida` or `.winlice` section; optionally encrypted |
| **Handler count** | FISH: ~60, TIGER: ~100, DOLPHIN: ~140, EAGLE: ~180, SHARK: ~220+ |

**Macro VM mode:** Instead of virtualizing whole functions, Themida virtualizes individual instruction sequences (3-10 instructions each). This creates many small VM entries scattered throughout the binary rather than one large VM call. Each entry uses the same VM dispatcher but has its own bytecode blob.

**Known weaknesses:**
- The handler dispatch pattern (`jmp [reg*scale + table]`) is recognizable and consistent across versions
- FISH VM handlers map 1:1 to x86 instructions — nearly direct translation
- Anti-dump can be bypassed with Scylla by dumping before the protection initializes
- The watermark string "Themida" or "WinLicense" often remains in section names or PE overlay

---

### VMProtect (VMProtect Software)

| Property | Detail |
|----------|--------|
| **Publisher** | VMProtect Software |
| **Platforms** | Windows x86/x64, Linux x64, macOS x64/ARM64 |
| **Protection layers** | Packing, import protection, code mutation, virtualization |
| **VM variants** | Multiple per-binary; each function can use a different VM instance |
| **Current version** | 3.8.x (2025-2026) |

**VM Architecture:**

VMProtect uses a **stack-based** bytecode interpreter (unlike Themida's register-based):

| Component | Implementation |
|-----------|---------------|
| **Dispatcher** | Large switch or computed goto; typically the biggest function in the binary |
| **Virtual PC (VIP)** | Register pointing into bytecode; incremented by handler |
| **Virtual stack pointer (VSP)** | Register (often `RBP`) managing the operand stack |
| **Virtual registers** | Memory slots on the real stack, addressed by VM bytecode operands |
| **Bytecode** | Stored in `.vmp0` / `.vmp1` sections; rolling-XOR encrypted |
| **Handler count** | 150-250+ handlers depending on complexity and mutation |

**Handler mutation:** Each handler is code-mutated — the same semantic operation (e.g., "add two stack values") is encoded with different instruction sequences across handlers. This breaks pattern-based handler identification.

**Bytecode encryption:** The bytecode stream is encrypted with a rolling key. The VM entry stub decrypts the bytecode at runtime before the dispatcher loop. The key is derived from the function's entry address.

**Ultra mode:** Nested virtualization — a VM's handlers are themselves virtualized by another VM instance. Two-layer trace required.

**Known weaknesses:**
- Stack-based architecture means every operation goes through push/pop → traces are verbose but regular
- NoVmp (open source) handles VMP 3.x; lifts to LLVM IR
- The VM entry point is always a `push <key>; call vmenter` pattern
- VMP's import protection redirects through per-call stubs that can be traced to resolve the real import

---

### Code Virtualizer (Oreans Technologies)

Same Oreans VM as Themida but sold as a standalone virtualizer without the packer/anti-debug layers. Same FISH/TIGER/DOLPHIN/EAGLE/SHARK VMs.

**Difference from Themida:** No packing, no anti-debug, no import protection. Just the VM. Easier to analyze because you skip layers 0-2.

---

### Enigma Protector

| Property | Detail |
|----------|--------|
| **Platforms** | Windows x86/x64 |
| **Protection** | Packing, import redirection, code encryption, basic VM, registration system |
| **Sections** | `.enigma1`, `.enigma2` |

**Weakness:** The VM is simpler than Themida/VMP (~40 handlers). Unpack first (standard `VirtualProtect` OEP technique), then the VM is tractable with Triton or manual analysis.

---

### Obsidium

| Property | Detail |
|----------|--------|
| **Platforms** | Windows x86/x64 |
| **Protection** | Anti-debug, anti-dump, code encryption, import protection, basic VM |

**Weakness:** Heavy anti-debug but weaker VM than Themida/VMP. ScyllaHide + standard unpacking usually sufficient.

---

## Compiler-Level Obfuscation

### LLVM-Obfuscator (OLLVM)

| Property | Detail |
|----------|--------|
| **Source** | Open-source (academic origin: University of Aix-Marseille) |
| **Mechanism** | Custom LLVM passes applied at compile time |
| **No protector to strip** — the obfuscation IS the compiled code |

**Passes:**

| Pass | What It Does | Counter |
|------|-------------|---------|
| **Bogus Control Flow (BCF)** | Inserts opaque predicates creating unreachable paths | Symbolic execution proves predicates constant → remove dead paths |
| **Control Flow Flattening (CFF)** | Flattens all blocks into a dispatcher loop | D-810 (IDA), deflat (Binary Ninja), manual state tracing |
| **Instruction Substitution (SUB)** | Replaces simple ops with algebraic equivalents | IDA optimizer, Miasm normalization, hrtng |
| **String Encryption** | Encrypts string literals, decrypts at runtime | Break on decryption function, log cleartext |
| **Indirect Branching** | Replaces direct jumps with pointer-based indirect jumps | Resolve targets via constant propagation or tracing |
| **MBA (Mixed Boolean-Arithmetic)** | `x + y` → `(x ^ y) + 2*(x & y)` and worse | SSPAM, Triton simplification, algebraic pattern matching |

---

### Hikari

Fork of OLLVM with additional passes: function call obfuscation, anti-class-dump (Objective-C), indirect global variable access. Same counter techniques as OLLVM.

---

### Pluto-Obfuscator

Modern LLVM-based obfuscator with MBA, CFF, indirect branching, and trap-based opaque predicates. Similar to OLLVM but targets newer LLVM versions (14+).

---

## Runtime Obfuscation Techniques

These are techniques used *by* protectors or *by* developers directly, independent of any specific product:

### Metamorphic Code

**What:** Code that rewrites itself into a functionally equivalent but syntactically different form at runtime. Each execution produces different instruction sequences.

**Counter:** Snapshot the code at a stable point (after self-modification completes), then analyze the snapshot. Or: trace the execution and analyze the trace rather than the code.

### Self-Modifying Code (SMC)

**What:** Code that modifies its own instructions during execution — typically decrypting the next basic block, executing it, then re-encrypting it.

**Counter:** Set hardware breakpoints (not software — int3 will be overwritten by SMC). Trace with HyperDbg or PIN. Dump pages at the moment they're executable.

### API Hashing

**What:** Instead of importing `CreateFileW` by name, the code hashes the name at runtime and walks the export table comparing hashes.

**Counter:** Identify the hash algorithm (commonly ROR13+ADD, CRC32, DJB2, FNV-1a), then pre-compute hashes for all ntdll/kernel32/user32 exports and match. HashDB (IDA plugin) automates this for known hash algorithms.

### Stack String Construction

**What:** Strings built character-by-character on the stack (`mov [rsp], 'H'; mov [rsp+1], 'e'; ...`) to avoid string table detection.

**Counter:** FLOSS (FireEye Labs Obfuscated String Solver) extracts stack strings automatically. Or: run the function and read the constructed string from the stack in the debugger.

### Dynamic Code Generation

**What:** The program generates code at runtime using `VirtualAlloc` + `memcpy` + `VirtualProtect(PAGE_EXECUTE_READWRITE)`. The generated code never exists on disk.

**Counter:** Break on `VirtualProtect` transitions to `PAGE_EXECUTE*`. Dump the generated page. The code exists in memory at execution time — you just need to capture it.

### Nanomites

**What:** Critical instructions are replaced with `int 3` (breakpoint). A parent process catches the exceptions via debug API and executes the original instruction in the exception handler.

**Counter:** Hook the exception handler to log what instruction it emulates, or patch the nanomites back to real instructions using the handler's logic as a guide.

---

## Kernel-Level Obfuscation

### PatchGuard / Kernel Patch Protection (KPP)

**What:** Windows kernel integrity monitor. Periodically checks critical kernel structures (SSDT, IDT, GDT, MSRs, critical function prologues) for unauthorized modifications. Triggers BSOD `CRITICAL_STRUCTURE_CORRUPTION` (0x109) on detection.

**Relevant to:** Anti-cheat driver analysis — some cheat drivers attempt to bypass PatchGuard to hook kernel functions.

**Key facts:**
- Timer-based checks with randomized intervals (every 5-10 minutes, unpredictable)
- The check context is obfuscated — it runs from a DPC, work item, or APC with an encrypted call chain
- The KPP context itself is encrypted in memory and decrypted only during checks
- KPP bypass is a moving target — Microsoft patches bypass techniques regularly

### Driver Signature Enforcement (DSE)

**What:** Windows only loads drivers with valid Microsoft-cross-signed certificates. Unsigned drivers get `STATUS_INVALID_IMAGE_HASH`.

**Bypass methods (for understanding, not recommendation):**
- Test-signing mode (`bcdedit /set testsigning on` — visible watermark)
- EFI bootloader modification (EfiGuard, before DSE initializes)
- Vulnerable signed driver exploitation (BYOVD — Bring Your Own Vulnerable Driver)

### Hypervisor-Based Protection

Some protectors (Denuvo, some anti-cheats) use a custom hypervisor:
- EPT (Extended Page Tables) to hide code pages
- VMFUNC for fast VM exits
- Hypervisor hooks on critical instructions (CPUID, RDMSR)

**Counter:** Nest inside another hypervisor (HyperDbg), or analyze from a hardware debugger / DMA where the hypervisor has no visibility.

---

## Quick Reference: Protector → Counter

| Protector | Primary Technique | Best Counter | Automated Tool |
|-----------|-------------------|-------------|----------------|
| **VMProtect** | Stack-based VM | Trace + lift | NoVmp, VMHunt, vtil |
| **Themida** (FISH) | Register-based VM (simple) | Handler mapping | Community scripts |
| **Themida** (SHARK) | Register-based VM (complex) | Trace + lift | Manual + Triton |
| **Code Virtualizer** | Same as Themida VM | Same as Themida | Same as Themida |
| **OLLVM CFF** | Control flow flattening | CFG recovery | D-810, deflat |
| **OLLVM MBA** | Algebraic obfuscation | Simplification | SSPAM, Triton |
| **OLLVM SUB** | Instruction substitution | Optimization | IDA, hrtng |
| **Enigma** | Packer + weak VM | Unpack + manual | Standard unpacking |
| **Obsidium** | Anti-debug + encryption | ScyllaHide + dump | Scylla, pe-sieve |
| **PatchGuard** | Kernel integrity | Analysis-only | Volatility, WinDbg |
| **Custom VM** | Varies | Manual handler RE | Triton, Miasm |

---

## Source: `knowledge/offset-methodology.md`

# Offset Finding and Maintenance Methodology

## When to Pattern Scan vs Hardcode

**Pattern scan** (preferred): any global pointer, vtable address, or function address that the compiler may relocate between builds. The instruction sequence referencing it is stable; the address it points to is not.

**Hardcode** (acceptable): struct field offsets within a known type. `m_iHealth` at `+0x43E0` inside `CPlayer` changes only when Respawn reorders the class — which happens less often than code relocations. Still document the source.

## Signature Construction

1. Open the function in IDA/Ghidra. Find the instruction that loads/references the value you need.
2. Copy the raw bytes of that instruction and 1-2 neighboring instructions for uniqueness.
3. Replace **RIP-relative displacements** (4 bytes after the opcode) with `??` wildcards — these change every build.
4. Replace **immediate addresses** and **jump targets** with `??` — also unstable.
5. Keep **opcode bytes** and **register encodings** — these are stable unless the compiler changes register allocation.

```
Example instruction:  48 8B 05 [A0 B3 2A 01]  ← MOV RAX, [rip+0x12AB3A0]
                      ^^^^^^^^ ^^^^^^^^^^^^^^
                      opcode   RIP displacement (changes every build)

Signature:           "48 8B 05 ?? ?? ?? ??"
```

Verify uniqueness: `find_all_code_patterns` should return exactly 1 hit. If multiple, extend the sig with more surrounding bytes.

## RIP-Relative Address Resolution

Most x64 instructions use RIP-relative addressing. The displacement is a **signed 32-bit integer** relative to the **end** of the instruction (i.e., the address of the next instruction).

```
hit        = address where the sig matched
disp_off   = offset from hit to the displacement bytes (e.g., 3 for LEA reg,[rip+??])
insn_len   = total instruction length (e.g., 7 for a 7-byte LEA)
displacement = read_int32(hit + disp_off)      ← signed!
resolved   = hit + insn_len + displacement
```

Common instruction shapes:

| Pattern | Instruction | disp_off | insn_len |
|---------|-------------|----------|----------|
| `48 8B 05 ?? ?? ?? ??` | MOV RAX, [rip+disp] | 3 | 7 |
| `48 8D 0D ?? ?? ?? ??` | LEA RCX, [rip+disp] | 3 | 7 |
| `48 8B 0D ?? ?? ?? ??` | MOV RCX, [rip+disp] | 3 | 7 |
| `E8 ?? ?? ?? ??` | CALL rel32 | 1 | 5 |
| `E9 ?? ?? ?? ??` | JMP rel32 | 1 | 5 |

## Pointer Chain Walking

Game data is often behind multiple levels of indirection:

```
base_address → entity_list_ptr → entity_ptr → field
```

Strategy:
1. Find the first pointer via sig scan + RIP resolution.
2. Dereference each level with `ru64`, checking for 0 at every step.
3. Document the full chain: `base + 0x... → deref → + 0x... → deref → + 0x...`
4. The final offset into the struct is typically a hardcoded field offset.

```cpp
uint64 entity_list = resolve_sig(p, base, size, SIG_ENTITY_LIST);  // sig scan
if (entity_list == 0) return;                                       // stale sig
uint64 list_ptr = p.ru64(entity_list);                              // deref level 1
if (list_ptr == 0) return;                                          // null
uint64 entity = p.ru64(list_ptr + cast<uint64>(index) * 0x8);      // deref level 2
if (entity == 0) return;                                            // null entry
int32 health = p.r32(entity + 0x43E0);                             // struct field
```

## Using struct_dump for Discovery

When you don't know a struct layout, read raw memory and classify fields:

```cpp
// In Perception IDE, the AI can use struct_dump tool:
// struct_dump(addr, size=0x100)
// Returns: offset, raw hex, heuristic type (pointer/vtable/float/int/null)
```

Look for:
- **Pointers**: values in the `0x7FF...` range (usermode x64)
- **VTable ptrs**: first 8 bytes of an object, pointing into .rdata
- **Floats**: values like `100.0`, `0.0`, `-1.0` that make sense as game state
- **Ints**: small values (health, ammo, team ID)

## Cross-Referencing with IDA/Ghidra

1. Find the ConVar or string that names the feature (e.g., `"cl_interp"`, `"m_iHealth"`).
2. Xref the string → find the registration function → find the global variable or struct field.
3. Verify the offset in the reversed SDK headers if available (e.g., `r5sdk/src/game/server/player.h`).
4. Remember: SDK headers may be from an older game version. Always verify with a live read.

## Offset Table Format

Maintain a structured offset file:

```cpp
// offsets.em — auto-resolved via pattern scans
// Last verified: 2025-06-15, game version 1.98

const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";
// LEA RCX, [rip+????] — loads CEntityList global
// Source: sub_1400ABCDE in IDA, xref from "cl_entitylist"

const string SIG_VIEW_MATRIX = "48 8D 05 ?? ?? ?? ?? 48 89 44 24 ?? F3 0F";
// LEA RAX, [rip+????] — loads view-projection matrix (16 floats)

const string SIG_LOCAL_PLAYER = "48 8B 05 ?? ?? ?? ?? 48 85 C0 74 ?? 48 8B 48";
// MOV RAX, [rip+????] — loads local player pointer

// Struct field offsets (hardcoded, verified against SDK)
const uint64 OFF_HEALTH   = 0x43E0;   // CPlayer::m_iHealth (int32)
const uint64 OFF_TEAM     = 0x0448;   // CBaseEntity::m_iTeamNum (int32)
const uint64 OFF_POSITION = 0x014C;   // CBaseEntity::m_vecAbsOrigin (vec3 float32)
const uint64 OFF_NAME     = 0x0589;   // CBaseEntity::m_iName (string ptr)
```

## What Breaks on Game Updates

| What | Stability | Why |
|------|-----------|-----|
| Pattern signatures | **High** | Instruction sequences rarely change unless the function is rewritten |
| RIP-relative resolved addresses | **None** | Absolute addresses change every build |
| Struct field offsets | **Medium** | Change when devs add/remove/reorder fields |
| VTable indices | **Medium** | Change when virtual functions are added/removed |
| Function addresses | **None** | Change every build — always use sigs |
| String literals | **High** | Rarely change — good anchor points for xrefs |

---

## Source: `knowledge/pcx-api-cheatsheet.md`

# Perception.cx Enma API Quick Reference

All natives are auto-registered. No import needed (except `import "vec"; import "color";` for those types).

## Proc API — Process Memory

```cpp
proc_t p = ref_process("game.exe");       // by name
proc_t p = ref_process(1234);              // by PID
bool alive = p.alive();
uint64 base = p.base_address();
uint64 peb  = p.peb();
uint32 pid  = p.pid();
bool valid  = p.is_valid_address(addr);
```

### Read Primitives
```cpp
uint8/16/32/64  p.ru8/ru16/ru32/ru64(uint64 addr);
int8/16/32/64   p.r8/r16/r32/r64(uint64 addr);
float32         p.rf32(uint64 addr);
float64         p.rf64(uint64 addr);
string          p.rs(uint64 addr, int32 max_chars);    // ASCII
string          p.rws(uint64 addr, int32 max_chars);   // UTF-16→UTF-8
array<uint8>    p.rvm(uint64 addr, uint64 size);       // bulk
```

### Write Primitives (gated: `write_memory`)
```cpp
bool p.wu8/wu16/wu32/wu64(uint64 addr, uintN v);
bool p.w8/w16/w32/w64(uint64 addr, intN v);
bool p.wf32(uint64 addr, float32 v);
bool p.wf64(uint64 addr, float64 v);
bool p.wvm(uint64 addr, array<uint8> bytes);
```

### Typed Reads (vec/quat/mat)
```cpp
vec2 p.read_vec2_fl32(uint64 addr);     // also: _fl64 variant
vec3 p.read_vec3_fl32(uint64 addr);
vec4 p.read_vec4_fl32(uint64 addr);
quat p.read_quat_fl32(uint64 addr);
mat4 p.read_mat4_fl32(uint64 addr);
// write variants: p.write_vec3_fl32(addr, v), etc. (gated)
```

### Modules
```cpp
uint64                base = p.get_module_base("module.dll");
uint64                size = p.get_module_size("module.dll");
array<module_info_t>  mods = p.get_module_list();
uint64                exp  = p.get_proc_address(base, "ExportName");
uint64                imp  = p.get_import_rdata_address(base, "ImportName");
// module_info_t: .name(), .base(), .size()
```

### Pattern Scanning
```cpp
uint64 hit = p.find_code_pattern(start, size, "48 8B 05 ?? ?? ?? ?? 48 85 C0");
array<uint64> hits = p.find_all_code_patterns(start, size, sig);
```

### Memory Scanning
```cpp
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
array<uint64> p.scan_u64(value, heap_only);
array<uint64> p.scan_u32(value, heap_only);
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
```

### VAD / Virtual Query
```cpp
vad_region_t r = p.virtual_query(addr);       // .start(), .size(), .protection()
array<vad_region_t> snap = p.get_vad_snapshot(heap_only);
```

### VM Alloc/Free (gated: `virtual_memory_operations`)
```cpp
uint64 page = p.alloc_vm(4096);
bool ok = p.free_vm(page);
```

## Render API — 2D Drawing

```cpp
import "vec";
import "color";

// Primitives
draw_line(vec2 a, vec2 b, color c, float64 thickness);
draw_rect(vec2 pos, vec2 size, color c, float64 thickness, float64 rounding, uint8 flags);
draw_rect_filled(vec2 pos, vec2 size, color c, float64 rounding, uint8 flags);
draw_circle(vec2 center, float64 radius, color c, float64 thickness, bool filled);
draw_arc(vec2 center, vec2 radii, float64 start, float64 sweep, color c, float64 thick, bool filled);
draw_triangle(vec2 a, vec2 b, vec2 c, color col, float64 thickness, bool filled);
draw_text(string text, vec2 pos, color c, int64 font, int32 effect, color effect_c, float64 effect_amt);
draw_bitmap(int64 bmp, vec2 pos, vec2 size, color tint, bool rounded);

// effect: 0=none, 1=shadow, 2=outline
// rounding_flags: bitmask, 15=all corners

// Fonts
int64 get_font18(); int64 get_font20(); int64 get_font24(); int64 get_font28();
int64 create_font(string path, float64 size, bool aa, bool color, array ranges);
float64 get_text_width(int64 font, string text, int32 maxw, int32 maxh);
float64 get_text_height(int64 font, string text, int32 maxw, int32 maxh);

// Viewport
float64 get_view_width();  float64 get_view_height();
float64 get_view_scale();  float64 get_fps();

// Clipping
clip_push(vec2 pos, vec2 size); clip_pop();

// Shaders (layout: "POSITION:0:FLOAT2, COLOR:0:FLOAT4")
int64 create_shader(string vs, string ps, string layout);
int64 create_compute_shader(string cs);

// Buffers
int64 create_vertex_buffer(uint32 stride, uint32 max, bool dynamic);
int64 create_index_buffer(uint32 max, bool use32, bool dynamic);
int64 create_constant_buffer(uint32 size);
```

## GUI API — Sidebar Widgets

```cpp
int64 sec = create_section("Section Name");
section_checkbox(sec, "Label", bool_ref);
section_slider_float(sec, "Label", float_ref, min, max);
section_slider_int(sec, "Label", int_ref, min, max);
section_button(sec, "Label", callback_fn);
section_text_input(sec, "Label", string_ref);
section_keybind(sec, "Label", key_ref);
section_color_picker(sec, "Label", color_ref);
section_dropdown(sec, "Label", index_ref, items_array);
section_label(sec, "Text");
section_separator(sec);
```

## Input API

```cpp
bool key_down       (int64 vk);      // host-debounced down state
bool key_raw_down   (int64 vk);      // OS-level pressed state
bool key_fired      (int64 vk);      // up->down this frame (one-shot)
bool key_toggle     (int64 vk);      // caps-lock-style toggle
bool key_singlepress(int64 vk);      // fired but suppressed if modifiers held
bool key_prev_down  (int64 vk);      // down state from previous frame

key_state_t  get_key_state(int64 vk); // atomic snapshot of all 6 flags
array<int32> get_keys_down();         // virtual-key codes currently pressed
string       get_recent_key_input();  // buffered text input (UTF-8)
string       get_key_name(int64 vk);  // localized key name (e.g. "F1")

vec2 get_mouse_pos();                 // render-window pixels
vec2 get_mouse_pos_desktop();         // desktop pixels (full screen)
vec2 get_mouse_delta();               // raw movement this frame
vec2 get_mouse_delta_desktop();       // desktop-space delta this frame
bool mouse_movement_received();       // any movement this frame
bool is_hovered(vec2 pos, vec2 size); // mouse inside rect
float64 get_scroll_delta();           // wheel ticks; positive = up
```

## CPU API

```cpp
string get_cpu_vendor();
float64 time_ms();     // monotonic milliseconds
float64 time_us();     // monotonic microseconds
int32 get_datetime_year/month/day/hour/minute/second();
```

## Zydis API — x86-64 Disassembler/Assembler

```cpp
zydis_insn_t insn = zydis_decode(bytes_array, addr);
// insn.mnemonic, insn.length, insn.operands[]
array<uint8> encoded = zydis_encode(mnemonic, operands);
```

## Unicorn API — x86-64 Emulation

```cpp
int64 uc = uc_create();
uc_mem_map(uc, addr, size, perms);
uc_mem_write(uc, addr, bytes);
uc_reg_write(uc, reg_id, value);
uc_emu_start(uc, begin, until, timeout, count);
uint64 val = uc_reg_read(uc, reg_id);
array<uint8> data = uc_mem_read(uc, addr, size);
uc_destroy(uc);
```

## Net API

```cpp
string body = http_get(url, headers_map);
string body = http_post(url, post_body, headers_map);
int64 ws = ws_connect(url); ws_send(ws, msg); string r = ws_recv(ws);
int64 sock = udp_create(); udp_send(sock, host, port, data); udp_recv(sock, buf, timeout);
```

## Win API

```cpp
array<window_t> wins = enum_windows();
// window_t: .hwnd(), .title(), .class_name(), .pid(), .rect()
send_key(int32 vk, bool down);
send_mouse(int32 button, bool down, int32 x, int32 y);
string clip = get_clipboard(); set_clipboard(text);
```

## Filesystem API

```cpp
string content = read_file(path);
bool ok = write_file(path, content);
bool exists = file_exists(path);
array<string> entries = list_dir(path);
bool ok = create_dir(path);
bool ok = delete_file(path);
```

## Sound API

```cpp
int64 snd = load_sound(path);   // .wav or .ogg
play_sound(snd);
```

## Lifecycle

```cpp
int64 main() {
    // return > 0 to stay loaded, <= 0 to unload
    register_routine(cast<int64>(my_fn), user_data);
    return 1;
}
void my_fn(int64 data) { /* called every frame */ }
unregister_routine(handle);
```

---

# New API Additions (Feb–June 2026 Changelogs)

## Custom Draw API — Direct GPU Access (D3D11)

Full custom shader pipeline on the Universal API. Write HLSL, create vertex
buffers, textures, render targets, depth buffers, and draw any primitive
topology directly from AngelScript/Enma. Custom draw commands respect draw
order with every existing render function. All resources are tracked
per-script and auto-cleaned on unload.

### Resource Creation (all return `uint64` handle, `0` on failure)
```cpp
uint64 create_shader(string vs_source, string ps_source, string layout);
uint64 create_vertex_buffer(uint32 stride, uint32 max_vertices, bool dynamic);
uint64 create_index_buffer(uint32 max_indices, bool is_32bit, bool dynamic);
uint64 create_constant_buffer(uint32 size);
uint64 create_blend_state(src, dst, op, src_alpha, dst_alpha, op_alpha);
uint64 create_sampler(filter, address_u, address_v);
uint64 create_texture(uint32 width, uint32 height, array<uint8> rgba_data);
uint64 create_render_target(uint32 width, uint32 height);
uint64 create_depth_buffer(uint32 width, uint32 height);
uint64 create_depth_stencil_state(bool depth_enable, bool depth_write, int compare_func);
uint64 create_rasterizer_state(int fill_mode, int cull_mode);
```

### Drawing
```cpp
custom_draw(shader, vb, data, vertex_count, topology,
            blend, sampler, texture, rt, cb, cb_data, cb_slot);
custom_draw_indexed(shader, vb, vert_data, vert_stride,
                    ib, index_data, index_count, topology,
                    blend, sampler, texture, rt, cb, cb_data, cb_slot);
```

### Render Target Operations
```cpp
custom_set_render_target(rt);
custom_set_render_target_ext(rt, depth_buffer);
custom_clear_render_target(rt, r, g, b, a);
custom_clear_depth_buffer(db);
custom_resolve_render_target(rt);     // copy RT -> backbuffer
```

### State Management
```cpp
custom_set_depth_stencil_state(ds);
custom_set_rasterizer_state(rs);
custom_set_viewport(x, y, w, h);                          // split-screen / PiP
custom_bind_textures(shader, slot0_tex, slot1_tex, ...);  // multi-texture
custom_bind_constant_buffers(shader, slot, cb, cb_data, cb_size);
```

### Mesh & Texture Loading
```cpp
load_obj_mesh(path);                  // returns vb + ib handles
create_texture_from_file(path);
create_dynamic_texture(width, height);
update_dynamic_texture(tex, rgba_data);
```

### Compute Shaders
```cpp
uint64 cs  = create_compute_shader(cs_source);
uint64 buf = create_structured_buffer(element_size, element_count, data);
dispatch_compute(cs, groups_x, groups_y, groups_z);
read_structured_buffer(buf);
```

### Backbuffer Capture
```cpp
uint64 tex = capture_backbuffer();    // texture handle of current frame
```

### Constants
```cpp
// Topology
TOPO_POINT_LIST, TOPO_LINE_LIST, TOPO_LINE_STRIP,
TOPO_TRIANGLE_LIST, TOPO_TRIANGLE_STRIP

// Compare funcs (depth stencil)
CMP_NEVER, CMP_LESS, CMP_EQUAL, CMP_LESS_EQUAL,
CMP_GREATER, CMP_NOT_EQUAL, CMP_GREATER_EQUAL, CMP_ALWAYS

// Fill modes
FILL_WIREFRAME, FILL_SOLID

// Cull modes
CULL_NONE, CULL_FRONT, CULL_BACK
```

### Layout String Format
Comma-separated `SEMANTIC:slot:TYPE` entries, e.g.
`"POSITION:0:FLOAT2, COLOR:0:FLOAT4"`.

### Key Features
- Indexed rendering with 16-bit and 32-bit index formats
- True 3D depth testing with configurable depth-stencil state
- Rasterizer state control (culling, wireframe)
- Custom viewports for split-screen / picture-in-picture
- Multi-texture and multi-constant-buffer binding
- Compute shaders with structured buffers
- OBJ mesh loading + dynamic texture updates
- Depth-enabled render targets, backbuffer capture for post-processing

### Example: Basic Colored Triangle
```angelscript
string vs = """
cbuffer cb : register(b0) { float4x4 proj; };
struct VS_IN  { float2 pos : POSITION; float4 col : COLOR; };
struct VS_OUT { float4 pos : SV_Position; float4 col : COLOR; };
VS_OUT main(VS_IN i) {
    VS_OUT o;
    o.pos = mul(float4(i.pos, 0, 1), proj);
    o.col = i.col;
    return o;
}
""";

string ps = """
struct PS_IN { float4 pos : SV_Position; float4 col : COLOR; };
float4 main(PS_IN i) : SV_Target { return i.col; }
""";

uint64 shader = create_shader(vs, ps, "POSITION:0:FLOAT2, COLOR:0:FLOAT4");
uint64 vb = create_vertex_buffer(24, 3, true);
uint64 blend = create_blend_state(BLEND_SRC_ALPHA, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD,
                                  BLEND_ONE, BLEND_INV_SRC_ALPHA, BLEND_OP_ADD);
```

### Example: Depth-Tested 3D Scene
```angelscript
uint64 db = create_depth_buffer(400, 300);
uint64 ds = create_depth_stencil_state(true, true, CMP_LESS);

custom_set_render_target_ext(rt, db);
custom_clear_depth_buffer(db);
custom_set_depth_stencil_state(ds);
```

## World-to-Screen (updated Feb 2026)

```cpp
bool world_to_screen_rowmajor(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
bool world_to_screen_transposed(vec3 world_pos, mat4 view_matrix, vec2 &out screen_pos);
```
- Use `world_to_screen_rowmajor` for row-major view matrices.
- Use `world_to_screen_transposed` for transposed (column-major) matrices.
- ⚠️ **DEPRECATED:** `source2_world_to_screen` — replace with the variants above.

## Matrix4x4 Double Precision (Feb 2026)

```cpp
mat4 m.readas_float(uint64 addr);      // float-precision read
mat4 m.readas_double(uint64 addr);     // double-precision read
bool m.writeas_float(uint64 addr, mat4 v);
bool m.writeas_double(uint64 addr, mat4 v);
```
- ⚠️ **DEPRECATED:** default `matrix4x4` read/write — use a precision-specific variant.

## Thread Priority Helpers (Feb 2026)

```cpp
set_thread_to_highest_priority();
set_thread_to_lowest_priority();
set_thread_to_normal_priority();
```

## Atomics (Feb 2026)

```cpp
atomic_int32 a;    // lock-free thread-safe 32-bit integer
atomic_int64 b;    // lock-free thread-safe 64-bit integer
```

## GUI Additions (Feb–Mar 2026)

```cpp
get_gui_position(float &out x, float &out y);   // GUI window position
get_gui_size(float &out w, float &out h);       // GUI window size

// List widget ops
list:get(...);              list:remove(...);
list:highlight(...);        list:remove_highlight(...);
list:hide(...);             list:show(...);
```

## Callbacks (Mar 2026)

```cpp
register_callback(string name, func, bool render_on_top = false);
// render_on_top=true renders on top of everything else
```

## Window Additions (Feb 2026)

```cpp
array<uint64> hwnds = get_all_hwnds();   // all window handles
```

## Fonts (Feb 2026)

```cpp
int64 create_font(string name, float64 size, array glyph_ranges);       // glyph_ranges optional
int64 create_font_mem(array<uint8> data, float64 size, array glyph_ranges); // glyph_ranges optional
```

## Input Additions (Feb 2026)

- Controller keybinds via **XINPUT** now supported.
- `get_mouse_delta()` now returns proper movement delta (fixed).

## Unicorn Emulator Updates (Mar 2026)

```cpp
// New hook types
UC_HOOK_INSN_INVALID    // invalid instructions
UC_HOOK_INTR            // software interrupts (INT3, syscalls)

uint64 status = uc_get_last_exception(uc);     // NTSTATUS, e.g. 0xC0000005
uint64 rip    = uc_get_exception_address(uc);  // RIP where exception occurred
```
- Null pointer access is now caught gracefully instead of crashing.

## Sound API — Full Audio Engine (Mar 2026)

44100Hz stereo, up to 64 simultaneous instances. WAV (PCM 8/16-bit) parsed
directly; MP3/AAC/WMA/FLAC decoded via Media Foundation. Auto-cleanup on
script unload.

```cpp
int64 snd = load_sound(path);
free_sound(snd);
play_sound(snd, bool loop);
stop_sound(snd);
stop_all_sounds();
set_sound_volume(snd, float vol);   // 0.0 – 1.0
set_sound_pan(snd, float pan);      // -1.0 (L) – +1.0 (R)
```

## Scan API Updates (Mar 2026)

Scan functions now return `array<uint64>@` directly (no `&out` params).
The `get_vad_snapshot` regression is fixed and returns proper values.

```cpp
array<uint64> p.scan_float(value, heap_only);
array<uint64> p.scan_double(value, heap_only);
array<uint64> p.scan_string("text", heap_only);
array<uint64> p.scan_wstring("text", heap_only);
array<uint64> p.scan_pointer(target_addr, heap_only);
```
- ⚠️ **REMOVED (never existed):** `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64`.

## Deprecated Functions Summary

| Deprecated | Replacement |
|---|---|
| `source2_world_to_screen` | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| default `matrix4x4` read/write | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | removed — use `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` |

---

## Source: `knowledge/pcx-doc-roots.md`

# PCX Documentation Roots

The authoritative source for Perception.cx scripting APIs in this toolkit is
the Enma documentation tree on `docs.perception.cx`:

1. **Enma (Perception.cx Enma API)**  
   Canonical entry point: `https://docs.perception.cx/perception/enma/readme.md`  
   Sub-pages follow the convention: `https://docs.perception.cx/perception/enma/<page>.md`

## What this means

- Every PCX API symbol used in generated code must be traceable to this Enma
  tree, or to the generated `knowledge/pcx-api-index.json` that is built from it.
- Do not use the local `docs/` copy as a primary authority; it is a drift-checked
  mirror. If a local doc and the live upstream disagree, the live upstream wins.
- The Enma *language* reference (grammar, types, addons) lives at
  `https://enma-1.gitbook.io/enma/` and is referenced for language semantics,
  but the PCX API surface itself comes only from the Enma root above.

## Navigating the trees

GitBook exposes a structured index at `https://docs.perception.cx/perception/llms.txt`.
Use it to discover the exact sub-page paths under the Enma root. In code, prefer
fetching the `.md` variant of any page so the model receives structured
markdown rather than rendered HTML.

## Generated index

`knowledge/pcx-api-index.json` is derived by scanning the local mirrors of the
pages under this root (plus the Enma addon docs that the Enma API
references). It exists so tools like `pcx symbol-check` and the
`mcp:pcx-knowledge` `validate_code` tool can catch invented API names without
performing a live fetch on every keystroke.

---

## Source: `knowledge/pcx-version-matrix.md`

# PCX API Version Matrix

This file maps each PCX API addition / change / removal to the version it landed in, so scripts that target older PCX runtimes know what's safe. Drawn from `docs/perception/changelogs.md`.

> **Read this before** committing to a script that must run on a specific PCX runtime version.

PCX ships **date-stamped rolling releases**, not semantic versions. The changelog
(`docs/perception/changelogs.md`) is keyed by release date and product line
(`Universal API` vs `Counter-Strike 2`). There is no `vX.Y` version number in any
shipped artifact, so this matrix uses the **changelog release date** as the version
anchor. When a `## How to Use` example writes `// Requires: PCX v<X.Y>+`, read the
placeholder as the corresponding **release date** (e.g. `// Requires: PCX 2026-03-16+`).

Two same-day Universal API posts are disambiguated as the changelog does — `(a)`
(earlier) and `(b)` (later). Where the changelog never dates an API but the cheatsheet
or per-API docs document it, the row reads `<= <earliest dated release that references it>`
or `unknown` — never a guessed date.

Machine-readable seed metadata for public Perception symbols lives in
`knowledge/perception-symbol-versions.json`. Keep that JSON and this narrative matrix
cross-linked: JSON is for tooling; this file is for historical context and rationale.

---

## How to Use This File

1. **Pin the target at the top of the script.** A one-line comment records the oldest
   runtime the script is allowed to load on:

   ```cpp
   // Requires: PCX 2026-03-17+   (custom-draw 3D: depth testing + compute shaders)
   ```

2. **Before using an API, check the matrix.** Find the API's row in
   `## API Matrix — By Category`. If its `Since` date is **after** your pin, either
   raise the pin or do not call it. If the `Deprecated/Removed In` column is set and
   your target is **at or after** that date, use the `Replacement` instead.

3. **Targeting multiple runtimes? Fall back gracefully.** PCX exposes no runtime
   version query (see next section), so multi-version support is done with
   preprocessor `#define` guards set from the SDK, gated by what you tested. Example:

   ```cpp
   // Build host passes the target via the SDK:
   //   define(engine, "PCX_2026_03_17", "1");   // only on >= 2026-03-17 builds
   #ifdef PCX_2026_03_17
       uint64 cs = create_compute_shader(cs_src);   // since 2026-03-17(a)
       dispatch_compute(cs, 64, 1, 1);
   #else
       // conservative path: CPU fallback, no compute shaders
   #endif
   ```

---

## Runtime Version Detection

**There is no documented API to ask the PCX runtime its version.** No
`get_version` / `api_version` / `client_version` / `build_version` native appears in
`docs/perception/*` or `knowledge/pcx-api-cheatsheet.md`. Do not invent one — a call to
a nonexistent native fails to compile (Enma) or aborts the script.

Use the **conservative approach**: drive feature availability from preprocessor
symbols the build host injects, set only after you have tested the target build.

```cpp
// ── SDK side (host C++), set per known-good target build ──
//   define(engine, "PCX_BUILD", "20260317");   // numeric YYYYMMDD of tested build
//   add_include_path(engine, "includes/");

// ── Script side ──
#ifndef PCX_BUILD
    #error "PCX_BUILD not defined — host must declare the tested runtime build"
#endif

#if PCX_BUILD >= 20260317
    // depth testing + compute shaders available (since 2026-03-17(a))
#elif PCX_BUILD >= 20260316
    // base custom-draw shader pipeline only (since 2026-03-16)
#else
    // pre-custom-draw: 2D primitives only
#endif
```

`#define`, `#ifdef`/`#ifndef`/`#if`/`#elif`/`#else`/`#endif`, and SDK-side
`define(engine, name, value)` are all documented in `docs/enma/lang-pre-processor.md`.
The numeric `YYYYMMDD` form lets you use `#if PCX_BUILD >= …` integer comparisons.
The runtime cannot self-report, so **the host is the source of truth** — never branch
on a value the script tries to read at runtime.

---

## API Matrix — By Category

Columns: `API` | `Since` | `Notes` | `Deprecated/Removed In` | `Replacement`.
Every `Since` cites the changelog release date or is marked `unknown` / `<= <date>`.

### Render — 2D Primitives & Fonts

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `draw_line` | `<= 2026-02-01` | Line, `thickness` arg. `docs/perception/render-api.md`. | — | — |
| `draw_rect` / `draw_rect_filled` | `<= 2026-02-01` | Rect with `rounding` + corner flags. | — | — |
| `draw_circle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_arc` | `<= 2026-02-01` | `radii`, `start`, `sweep`. | — | — |
| `draw_triangle` | `<= 2026-02-01` | `filled` bool. | — | — |
| `draw_text` | `<= 2026-02-01` | `effect` 0=none/1=shadow/2=outline. | — | — |
| `draw_bitmap` | `<= 2026-02-01` | Tinted bitmap blit. | — | — |
| `draw_four_corner_gradient` | unknown | In `docs/perception/render-api.md` but never named in the changelog. Treat as `<= 2026-02-01` core. | — | — |
| `draw_polygon` | unknown | In `docs/perception/render-api.md`; no changelog row. Treat as `<= 2026-02-01` core. | — | — |
| `get_font18/20/24/28`, `get_text_width`, `get_text_height` | `<= 2026-02-01` | Built-in font handles; predate the window. | — | — |
| `create_font` / `create_font_mem` — optional `glyph_ranges` arg | `2026-02-03(b)` | Optional `glyph_ranges` added in a combined historical changelog row. Older builds: no `glyph_ranges` parameter. | — | — |
| Font loading latency | `2026-02-03(b)` | "Font loading now instant" + render backend optimized (changelog `Feb 3 (b) → Render Engine`). Behavior change, not a new symbol. | — | — |
| Script render order | `2026-02-12` | Changed: "newly created callbacks render first" (changelog `Feb 12 → Render System`). Order reversed vs earlier builds. | — | — |

### Render — Custom Draw (Direct D3D11 / GPU)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` | `2026-03-16` | Base custom-draw pipeline — HLSL VS/PS compiled at runtime, all primitive topologies (changelog `Mar 16 → Custom Draw API — Direct GPU Access`). | — | — |
| Custom draw on CS2 product | `2026-03-16` (CS2) | Same Custom Draw API pushed to the CS2 line (changelog `Mar 16 — Counter-Strike 2`). | — | — |
| `create_index_buffer`, `custom_draw_indexed` | `2026-03-17(a)` | Indexed drawing, 16-bit and 32-bit index buffers (changelog `Mar 17 (a) → Indexed Drawing`). | — | — |
| `create_depth_buffer`, `create_depth_stencil_state`, `custom_set_depth_stencil_state`, `custom_clear_depth_buffer`, `custom_set_render_target_ext` | `2026-03-17(a)` | Depth testing + depth-enabled render targets (changelog `Mar 17 (a) → Depth Testing`, `Depth-Enabled Render Targets`). | — | — |
| `create_rasterizer_state`, `custom_set_rasterizer_state` | `2026-03-17(a)` | Cull / fill mode, wireframe (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `custom_set_viewport` | `2026-03-17(a)` | Split-screen / picture-in-picture (changelog `Mar 17 (a) → Custom Viewports`). | — | — |
| `custom_bind_textures` (multi-texture) | `2026-03-17(a)` | Bind multiple textures to one shader (changelog `Mar 17 (a) → Multi-Texture Binding`). | — | — |
| `custom_bind_constant_buffers` (multi-CB) | `2026-03-17(a)` | Multiple constant buffers to different slots (changelog `Mar 17 (a) → Multi-Constant-Buffer Binding`). | — | — |
| `create_compute_shader`, `create_structured_buffer`, `dispatch_compute`, `read_structured_buffer` | `2026-03-17(a)` | GPU compute from script (changelog `Mar 17 (a) → Compute Shaders`). | — | — |
| `load_obj_mesh` | `2026-03-17(a)` | Loads `.obj`, returns vb+ib handles (changelog `Mar 17 (a) → OBJ Mesh Loading`). | — | — |
| `create_dynamic_texture`, `update_dynamic_texture`, `create_texture_from_file` | `2026-03-17(a)` | Runtime-updatable textures (changelog `Mar 17 (a) → Dynamic Textures`). | — | — |
| `capture_backbuffer`, `custom_resolve_render_target` | `2026-03-17(a)` | Backbuffer capture for post-processing (changelog `Mar 17 (a) → Backbuffer Capture`). | — | — |

### Render — Custom Draw Constants & Enums

| Symbol group | Since | Notes | Deprecated/Removed In | Replacement |
|--------------|-------|-------|-----------------------|-------------|
| `BLEND_SRC_ALPHA`, `BLEND_INV_SRC_ALPHA`, `BLEND_ONE`, `BLEND_OP_ADD`, … (blend constants) | `2026-03-16` | Args to `create_blend_state`; ship with the base pipeline (changelog `Mar 16`). | — | — |
| Layout string format `"SEMANTIC:slot:TYPE"` | `2026-03-16` | Vertex layout for `create_shader` (changelog `Mar 16 → Shaders`, "Layout defined with format string"). | — | — |
| `TOPO_POINT_LIST`, `TOPO_LINE_LIST`, `TOPO_LINE_STRIP`, `TOPO_TRIANGLE_LIST`, `TOPO_TRIANGLE_STRIP` | `2026-03-16` | All primitive topologies present at base pipeline (changelog `Mar 16 → All Primitive Topologies`). | — | — |
| `CMP_NEVER` … `CMP_ALWAYS` (depth compare funcs) | `2026-03-17(a)` | Args to `create_depth_stencil_state` (changelog `Mar 17 (a) → Depth Testing`). | — | — |
| `FILL_WIREFRAME`, `FILL_SOLID` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |
| `CULL_NONE`, `CULL_FRONT`, `CULL_BACK` | `2026-03-17(a)` | Args to `create_rasterizer_state` (changelog `Mar 17 (a) → Rasterizer State`). | — | — |

### Proc — Memory Read / Write & Typed Reads

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `ref_process` (by name / by PID), `alive`, `base_address`, `peb`, `pid`, `is_valid_address` | `<= 2026-02-01` | Process handle + validity. `docs/perception/proc-api.md`. | — | — |
| `ru8/16/32/64`, `r8/16/32/64`, `rf32/64` | `<= 2026-02-01` | Scalar read primitives. | — | — |
| `rs`, `rws`, `rvm` | `<= 2026-02-01` | ASCII / UTF-16 / bulk reads. | — | — |
| `wu8/16/32/64`, `w8/16/32/64`, `wf32/64`, `wvm` | `<= 2026-02-01` | Write primitives (gated: `write_memory`). | — | — |
| `read_vec2/3/4_fl32`, `read_vec2/3/4_fl64`, `read_quat_fl32/64`, `read_mat4_fl32/64` + write mirrors | unknown | Documented in `docs/perception/proc-api.md` but **not named in the changelog**. Do not date precisely; treat as `<= 2026-02-01` core typed reads. Distinct from the `mat4` method `readas_*` below. | — | — |
| `get_module_base/size/list`, `get_proc_address`, `get_import_rdata_address` | `<= 2026-02-01` | Core module surface. | — | — |
| `find_code_pattern`, `find_all_code_patterns` | `<= 2026-02-01` | Core scanning. Executable-section-only + single-hit fixes landed `2026-02-12 → RE Tools`. | — | — |
| `scan_float`, `scan_double`, `scan_string`, `scan_wstring`, `scan_pointer` | `2026-03-14` | Added (changelog `Mar 14 → VAD / Memory Scan API Fixes`: "Added missing functions"). | — | — |
| Scan return shape | `2026-03-14` | Changed: scan functions now return `array<uint64>@` directly, no `&out` params (changelog `Mar 14`). Pre-`2026-03-14` callers used the old `&out` form. | — | — |
| `get_vad_snapshot` | `<= 2026-02-01` | Existed earlier but returned all-zero fields until fixed `2026-03-14` (changelog `Mar 14`: "Fixed `get_vad_snapshot` returning all-zero fields"). | — | — |
| `virtual_query`, `vad_region_t` | `<= 2026-02-01` | Core VAD query. | — | — |
| `alloc_vm` / `free_vm` | unknown | Allocation API existed pre-window; `2026-03-20` reworked it ("no longer causes BSODs", changelog `Mar 20 → Allocation API`). Requires CFG disabled + Insecure API enabled to execute allocated memory. | — | — |

### Proc / Threading — Matrix Precision, Atomics, Thread Priority

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `mat4.readas_float` / `readas_double` / `writeas_float` / `writeas_double` | `2026-02-03(b)` | Matrix4x4 double-precision read/write variants from a combined historical changelog row. | — | — |
| default `matrix4x4` read/write (no precision suffix) | `<= 2026-02-03(a)` | — | `2026-02-03(b)` (deprecated) | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` |
| `atomic_int32`, `atomic_int64` | `2026-02-03(b)` | Lock-free shared state (changelog `Feb 3 (b) → AngelScript → Atomic API`). AngelScript-only entry. | — | — |
| `set_thread_to_highest_priority` / `lowest` / `normal_priority` | `2026-02-03(b)` | Thread priority helpers (changelog `Feb 3 (b) → AngelScript`). AngelScript-only entry. | — | — |

### World-to-Screen

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `source2_world_to_screen` (no viewport) | `<= 2026-02-01` | Original Source 2 W2S. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `source2_world_to_screen` — optional `viewport` arg | `2026-02-03(a)` | Added optional `const vector2 &in viewport = vector2(0,0)` (changelog `Feb 3 (a) → AngelScript`). Superseded one release later. | `2026-02-03(b)` (deprecated) | `world_to_screen_rowmajor` / `world_to_screen_transposed` |
| `world_to_screen_rowmajor` | `2026-02-03(b)` | Replaces `source2_world_to_screen` for row-major matrices (combined historical changelog row, "migration required"). | — | — |
| `world_to_screen_transposed` | `2026-02-03(b)` | New, for transposed/column-major matrices (changelog `Feb 3 (b)`). | — | — |

### Input

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `is_key_down`, `is_key_pressed`, `is_key_released` | `<= 2026-02-01` | Legacy keyboard state functions. | `2026-02-12` (deprecated) | `key_down` / `key_fired` / `key_toggle` |
| `is_mouse_down` | `<= 2026-02-01` | Legacy mouse button check. | `2026-02-12` (deprecated) | `key_down` with `vk::lbutton` / `vk::rbutton` |
| `key_down`, `key_fired`, `key_toggle`, `key_raw_down` | `2026-02-12` | Current unified keyboard and mouse button state queries. | — | — |
| `get_mouse_delta` | `<= 2026-02-01` | Existed earlier; behavior fixed `2026-02-12` to return proper movement delta instead of screen-space delta (changelog `Feb 12 → Input System`). | — | — |
| Controller keybinds (XINPUT) | `2026-02-12` | XINPUT controller keybind support added (changelog `Feb 12 → Input System`). | — | — |
| `get_gui_position(float &out x, float &out y)`, `get_gui_size(float &out w, float &out h)` | `2026-02-12` | Added (changelog `Feb 12 → AngelScript`). | — | — |
| `get_gui_pos` (legacy) | `<= 2026-02-12` | Position bug fixed `2026-03-17(b)` (changelog `Mar 17 (b) → AngelScript`, "Fixed `get_gui_pos` position issue"). Prefer `get_gui_position`. | — | `get_gui_position` |

### GUI — Sections, Widgets, Lists, Callbacks

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `create_section` | `<= 2026-02-01` | Returns section handle. `docs/perception/gui-api.md`. | — | — |
| `section_checkbox`, `section_slider_float`, `section_slider_int` | `<= 2026-02-01` | Toggle + numeric inputs. | — | — |
| `section_button`, `section_text_input`, `section_keybind` | `<= 2026-02-01` | Action / text / key-capture widgets. | — | — |
| `section_color_picker`, `section_dropdown` | `<= 2026-02-01` | Color ref / indexed dropdown. | — | — |
| `section_label`, `section_separator` | `<= 2026-02-01` | Static layout elements. | — | — |
| `list:get`, `list:remove`, `list:highlight`, `list:remove_highlight`, `list:hide`, `list:show` | `2026-02-17` | List widget op set added (changelog `Feb 17 → GUI`). | — | — |
| List widget selected-index correctness | `2026-02-03(a)` | Fixed: selected index becoming incorrect on add/remove (changelog `Feb 3 (a) → GUI`). | — | — |
| `register_callback` — optional `bool render_on_top = false` | `2026-03-17(b)` | Added (changelog `Mar 17 (b) → AngelScript`). Older builds: no `render_on_top` argument. | — | — |
| Taskbar (top-middle), force-on-top toggles | `2026-03-30(b)` | GUI taskbar for GUI/Analyzer/Editor/Console (changelog `Mar 30 (b) → GUI`). UI feature, not a script symbol. | — | — |
| Force render key (RE Tools while UI hidden) | `2026-03-18` | Configurable keybind (changelog `Mar 18 → GUI`). UI feature. | — | — |

### Sound

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `load_sound`, `free_sound`, `play_sound`, `stop_sound`, `stop_all_sounds`, `set_sound_volume`, `set_sound_pan`, `play_sound(..., loop=true)` | `2026-03-14` | Entire Sound API is new in this release — waveOut mixer, 44100Hz stereo, ≤64 instances, WAV direct + MF decode (changelog `Mar 14 → Sound API (new)`). No sound API exists before `2026-03-14`. | — | — |

### Net

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `http_get`, `http_post`, `ws_connect`, `ws_send`, `ws_recv`, `udp_create`, `udp_send`, `udp_recv` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/net-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core; do not assert a precise version. | — | — |

### Win

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `enum_windows`, `window_t`, `send_key`, `send_mouse`, `get_clipboard`, `set_clipboard` | `<= 2026-02-01` | Core Win API. `docs/perception/win-api.md`. | — | — |
| `get_all_hwnds()` | `2026-02-01` | Added in a combined historical changelog row ("returns all window handles"). | — | — |

### Filesystem

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `read_file`, `write_file`, `file_exists`, `list_dir`, `create_dir`, `delete_file` | unknown | Documented in `knowledge/pcx-api-cheatsheet.md` / `docs/perception/filesystem-api.md`; **no changelog row dates them**. Treat as `<= 2026-02-01` core. (Note: the same names also appear as IDE-AI tools in the changelog — those are tooling, not the script FS API.) | — | — |

### CPU / Time

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `get_cpu_vendor`, `time_ms`, `time_us`, `get_datetime_*` | `<= 2026-02-01` | Core CPU/time surface. `docs/perception/cpu-api.md`. | — | — |

### Zydis (disassembler / assembler)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `zydis_decode`, `zydis_encode`, `zydis_insn_t` | `<= 2026-02-01` | Core. `docs/perception/zydis-api.md`. | — | — |

### Unicorn (x86-64 emulation)

| API | Since | Notes | Deprecated/Removed In | Replacement |
|-----|-------|-------|-----------------------|-------------|
| `uc_create`, `uc_mem_map`, `uc_mem_write/read`, `uc_reg_write/read`, `uc_emu_start`, `uc_destroy` | `<= 2026-02-01` | Core emulation surface. `docs/perception/unicorn-api.md`. | — | — |
| `UC_HOOK_INSN_INVALID` | `2026-03-18` | Invalid instructions stop emulation with a logged message (changelog `Mar 18 → AngelScript API — Unicorn Emulator`). | — | — |
| `UC_HOOK_INTR` | `2026-03-18` | Software interrupts (INT3, syscalls) stop emulation cleanly (changelog `Mar 18`). | — | — |
| `uc_get_last_exception(handle)` | `2026-03-18` | Returns NTSTATUS (e.g. `0xC0000005`) (changelog `Mar 18`). | — | — |
| `uc_get_exception_address(handle)` | `2026-03-18` | Returns RIP at exception (changelog `Mar 18`). | — | — |
| Null-pointer access handling | `2026-03-18` | Changed: caught gracefully, emulation stops instead of crashing (changelog `Mar 18`). | — | — |

### Platform / Engine (non-API capabilities affecting scripts)

| Capability | Since | Notes | Deprecated/Removed In | Replacement |
|------------|-------|-------|-----------------------|-------------|
| 32-bit games support | `2026-03-08` | Added (changelog `Mar 8`). Scripts targeting x86 processes require `>= 2026-03-08`. | — | — |
| Fullscreen mode (universal) | `2026-03-20` | Engine + overlay support for all games (changelog `Mar 20 → Perception Engine`). | — | — |
| Extensions system (`.as` in `extensions/`) | `2026-03-14` | Lifecycle hooks, AI-pipeline hooks, widget/platform/editor APIs (changelog `Mar 14 → Extensions`). | — | — |
| `hash_map` global-init | `<= 2026-02-01` | Reference issue when initialized as global fixed `2026-02-01` (changelog `Feb 1 → AngelScript`). | — | — |
| Overlay protection modes (Disabled / Default / Perceptproof) | `2026-03-31(b)` | Three-level dropdown (changelog `Mar 31 (b) → Perceptproof Overlay Protection`). | — | — |
| Stream Proof / Anti-Screenshot toggle | `2026-03-30(a)` | Re-added enable/disable option (changelog `Mar 30 (a)`); note `2026-03-30(b)` hardened it so stream proof "cannot be disabled". | — | — |
| Config/data encrypted as `.pak` | `2026-03-18` | All config + state encrypted (changelog `Mar 18 → Security`). Clear `Documents/My Games` before this update. | — | — |

---

## Removed / Deprecated APIs

| API | Status | Since | Replacement | Source row |
|-----|--------|-------|-------------|------------|
| `source2_world_to_screen` | Deprecated | `2026-02-03(b)` | `world_to_screen_rowmajor` (row-major) / `world_to_screen_transposed` (transposed/column-major) | combined historical changelog row; also `Mar 16` cheatsheet note |
| default `matrix4x4` read/write (no precision suffix) | Deprecated | `2026-02-03(b)` | `readas_float` / `readas_double` / `writeas_float` / `writeas_double` | changelog `Feb 3 (b) → Deprecated` |
| `scan_bytes`, `scan_all_bytes`, `scan_all_u32`, `scan_all_u64` | Removed (never actually existed) | `2026-03-14` | `scan_float` / `scan_double` / `scan_string` / `scan_wstring` / `scan_pointer` | changelog `Mar 14 → VAD / Memory Scan API Fixes`, "Removed nonexistent functions from docs" |
| Legacy RE tools + old chatbot | Removed | `2026-03-08` | New RE tools GUI + IDE AI assistant (same release) | changelog `Mar 8` |
| IDE + Analyzer | Discontinued | `Enma Open Beta — Phase 2 (May 2026)` | Perception MCP (60-70+ tools) | changelog `Enma Open Beta — Phase 2` |

`scan_bytes` and friends were doc-only ghosts — they never shipped, so calling them
fails on **every** build. The `Since` of `2026-03-14` marks when they were struck from
the docs, not when they worked.

---

## Language Version Quirks

PCX changelogs have historical labels for multiple scripting front-ends. This
toolkit indexes and validates only Enma and AngelScript; exact per-feature
introduction dates inside an unversioned language reference are marked `unknown`.

### Front-end split history

| Era | Languages | Evidence |
|-----|-----------|----------|
| `<= 2026-03` | AngelScript plus historical non-indexed bindings | Changelog entries split between `AngelScript` and combined labels throughout Feb-Mar 2026. Treat combined labels as changelog provenance, not as a supported toolkit target. |
| `Enma Open Beta — Phase 2 (May 2026)` | Enma (new, proprietary AOT/JIT) added | Changelog `Enma Open Beta — Phase 2`: "Perception's proprietary programming language, built from scratch … compiles to native machine code". |

**AngelScript scope notes** (from the changelog's section headers):

| Feature | Scope at introduction | Since |
|---------|-----------------------|-------|
| `get_all_hwnds()` | AngelScript in this toolkit | `2026-02-01` |
| `create_font` / `create_font_mem` `glyph_ranges` | AngelScript in this toolkit | `2026-02-03(b)` |
| `mat4.readas_*` / `writeas_*` precision variants | AngelScript in this toolkit | `2026-02-03(b)` |
| `world_to_screen_rowmajor` / `_transposed` | AngelScript in this toolkit | `2026-02-03(b)` |
| `atomic_int32` / `atomic_int64` | **AngelScript only** | `2026-02-03(b)` |
| `set_thread_to_*_priority` | **AngelScript only** | `2026-02-03(b)` |
| `hash_map` global-init fix | **AngelScript only** | `2026-02-01` |
| `get_gui_position` / `get_gui_size` | **AngelScript only** | `2026-02-12` |
| `register_callback` `render_on_top` | **AngelScript only** | `2026-03-17(b)` |
| Unicorn `UC_HOOK_*`, `uc_get_*_exception*` | **AngelScript only** | `2026-03-18` |

Do not infer support for any non-indexed binding from these historical labels.

### Enma

Enma is documented in `docs/enma/` as a single unversioned reference. The only dated
anchor is the changelog's `Enma Open Beta — Phase 2 (May 2026)`. Every Enma language
feature below is therefore `<= Enma Open Beta Phase 2 (May 2026)`; an exact
introduction version is `unknown`.

| Feature | Available | Notes / source |
|---------|-----------|----------------|
| Full-module AOT + JIT to native x64 | `<= Enma Open Beta Phase 2 (May 2026)` | changelog `Enma Open Beta — Phase 2`; `docs/enma/llms-language.md §0` |
| Annotations (`[[...]]`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-annotations.md` |
| FFI (`[[dll(...)]]`, requires `PERM_FFI`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → FFI` |
| Coroutines (`coroutine` / `yield` / `coroutine_t`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-advanced.md → Coroutines`; runtime-auto-registered per `addon-core.md` |
| `defer`, `match`, `goto`, exceptions | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §5` |
| Atomic types (`aint8/16/32/64`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/llms-language.md §2`; `addon-atomic.md` |
| Preprocessor (`#define`, `#if`/`#ifdef`, `#include`, SDK `define()`) | `<= Enma Open Beta Phase 2 (May 2026)`; exact intro `unknown` | `docs/enma/lang-pre-processor.md` |

No Enma changelog predates the May 2026 Open Beta Phase 2 post, so anything finer than
"present in Open Beta Phase 2" is a guess and is left `unknown` here.

Documentation gap: publish an Enma language/API changelog or per-page `Introduced in`
metadata before using this matrix for compatibility decisions across Perception builds.
Until then, this toolkit records exact Enma introduction versions as `unknown` rather
than guessing from unversioned reference pages.

### AngelScript

PCX's AngelScript dialect is the historical default (pre-Enma). Feature deltas that
are dated land in the AS-specific rows of the matrix above (atomics, thread priority,
`render_on_top`, Unicorn hooks, etc.). The base AngelScript language itself is the
upstream AngelScript spec; PCX does not changelog core-language grammar changes.

## Release Timeline Index

Reverse-chronological. Each row lists the script-facing API surface a release
introduced or changed, so a `// Requires:` pin can be picked from the oldest
release carrying every API a script needs. Pure IDE/Analyzer/decompiler internals
(no script API) are omitted; see `docs/perception/changelogs.md` for the full text.

| Release | Script-facing API added / changed |
|---------|-----------------------------------|
| `Enma Open Beta — Phase 2 (May 2026)` | Enma language added (AOT/JIT); Perception MCP (60-70+ tools); IDE + Analyzer discontinued |
| `2026-04-06` | Analyzer memory usage reduced; no script-facing API changes |
| `2026-03-31(b)` | Overlay protection modes: Disabled / Default / Perceptproof |
| `2026-03-30(b)` | GUI taskbar + force-on-top; stream proof hardened (no longer disableable) |
| `2026-03-30(a)` | Stream Proof / Anti-Screenshot enable-disable toggle re-added |
| `2026-03-20` | Fullscreen mode (universal); `alloc_vm`/`free_vm` rework (CFG-disable + Insecure API to execute) |
| `2026-03-18` | Unicorn `UC_HOOK_INSN_INVALID`, `UC_HOOK_INTR`, `uc_get_last_exception`, `uc_get_exception_address`, graceful null deref; config `.pak` encryption; GUI force render key |
| `2026-03-17(b)` | `register_callback` `render_on_top` arg; `get_gui_pos` position fix |
| `2026-03-17(a)` | Custom Draw 3D/compute: `create_index_buffer`, `custom_draw_indexed`, `create_depth_buffer`/`create_depth_stencil_state`, `custom_set_render_target_ext`, `create_rasterizer_state`, `custom_set_viewport`, `custom_bind_textures`, `custom_bind_constant_buffers`, `create_compute_shader`/`dispatch_compute`/`create_structured_buffer`/`read_structured_buffer`, `load_obj_mesh`, dynamic textures, `capture_backbuffer`, `custom_resolve_render_target` |
| `2026-03-16` | Custom Draw base pipeline: `create_shader`, `create_vertex_buffer`, `create_constant_buffer`, `create_blend_state`, `create_sampler`, `create_texture`, `create_render_target` (Universal + CS2) |
| `2026-03-14` | Sound API (entire surface); scan `scan_float/double/string/wstring/pointer` + `array<uint64>@` return; `get_vad_snapshot` fix; `scan_bytes`/`scan_all_*` struck from docs; Extensions system |
| `2026-03-11` | Combined API IntelliSense; multi-root workspace |
| `2026-03-08` | 32-bit games support; legacy RE tools + old chatbot removed |
| `2026-02-17` | GUI list ops: `list:get/remove/highlight/remove_highlight/hide/show` |
| `2026-02-12` | XINPUT controller keybinds; `get_mouse_delta` fix; `get_gui_position`/`get_gui_size`; render order reversed |
| `2026-02-03(b)` | `world_to_screen_rowmajor`/`_transposed` (deprecate `source2_world_to_screen`); `mat4.readas_*`/`writeas_*` (deprecate default matrix r/w); `atomic_int32/64`; `set_thread_to_*_priority`; `create_font`/`create_font_mem` `glyph_ranges`; instant font load |
| `2026-02-03(a)` | `source2_world_to_screen` optional `viewport` arg; list selected-index fix |
| `2026-02-01` | `get_all_hwnds()`; `hash_map` global-init fix |
| `<= 2026-02-01` | Core surfaces (proc r/w + typed reads, render 2D, GUI sections, input, net, win, filesystem, CPU/time, Zydis, Unicorn base) predate the dated changelog window |

---

## Cross-References

- `docs/perception/changelogs.md` — the live primary source; every `Since` here traces to a dated row in it. Re-read it when a new release lands and update this matrix.
- `knowledge/pcx-api-cheatsheet.md` — the full current API surface this matrix versions.
- `docs/perception/render-api.md`, `proc-api.md`, `gui-api.md`, `input-api.md`, `sound-api.md`, `net-api.md`, `win-api.md`, `filesystem-api.md`, `unicorn-api.md`, `zydis-api.md`, `cpu-api.md`, `custom-draw-api.md`, `extensions-api.md` — per-API signatures.
- `docs/enma/llms-language.md`, `lang-pre-processor.md`, `lang-annotations.md`, `lang-advanced.md` — Enma language reference for the Language Version Quirks section.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the 12 rules every script in this repo follows.

---

## Source: `knowledge/perception-forum-insights.md`

# Perception Forum Insights

Derived from a targeted authenticated read-only crawl of Perception forum pages
on 2026-06-23. Treat this file as secondary operational context, not as an API
contract. The official docs, generated API index, and local validators remain
authoritative for exact Enma and AngelScript symbols.

Do not copy forum text verbatim into generated answers. Use these notes to route
context, identify likely stale docs, and decide which official source to verify.

## Source Threads

| Topic | Forum Source |
|-------|--------------|
| Enma beta announcement | <https://perception.cx/threads/open-beta-perception-enma.1149/> |
| Overlay compatibility note | <https://perception.cx/threads/new-overlay-information-05-27-2026.1171/> |
| Official GitBook pointer | <https://perception.cx/threads/official-gitbook-documentation-perception-v2.712/> |
| Client common issues | <https://perception.cx/threads/perception-client-self-help-guide-for-common-issues.760/> |
| Changelog 2026-04-06 | <https://perception.cx/threads/changelog-%E2%80%93-04-6-2026.1059/> |
| Changelog 2026-04-01 | <https://perception.cx/threads/changelog-%E2%80%93-04-1-2026.1050/> |
| Changelog 2026-03-31 | <https://perception.cx/threads/changelog-%E2%80%93-03-31-2026.1044/> |
| Changelog 2026-03-30 | <https://perception.cx/threads/changelog-%E2%80%93-03-30-2026.1040/> |
| Changelog 2026-03-20 | <https://perception.cx/threads/changelog-3-20-2026.1009/> |
| Changelog 2026-03-17 | <https://perception.cx/threads/changelog-3-17-2026.1000/> |
| Changelog 2026-03-16 | <https://perception.cx/threads/changelog-3-16-2026.996/> |
| Changelog 2026-03-14 | <https://perception.cx/threads/changelog-3-14-2026.983/> |
| Changelog 2026-02-17 | <https://perception.cx/threads/changelog-2-17-2026.921/> |
| Changelog 2026-02-12 | <https://perception.cx/threads/changelog-2-12-2026.905/> |
| Changelog 2026-02-01 | <https://perception.cx/threads/changelog-2-1-2026.878/> |

## Enma Rollout Signals

- Enma is Perception's own script language and is positioned as the next major
  PCX development path. Load `docs/perception/readme.md`,
  `docs/perception/lifecycle-and-routines.md`, and the generated Enma context
  pack before answering Enma questions.
- The forum announcement points to both the Enma GitBook and the Perception Enma
  docs. If the forum and local mirror disagree, verify against
  `docs/perception/readme.md` plus the relevant `docs/perception/*.md` API page,
  or the live official docs before asserting behavior.
- The announcement describes Enma as native-compiled rather than interpreted.
  For LLM routing, prefer Enma-specific lifecycle, imports, value types, and
  compile-time semantics over AngelScript habits.
- The SDK was described as following after language maturity. Do not imply that
  every embedding SDK feature is available inside PCX scripts unless the local
  PCX docs or API index prove it.

## AngelScript And Universal API Changelog Signals

- 2026-03-16 and 2026-03-17 expanded AngelScript Custom Draw into a D3D11-style
  GPU pipeline: shaders, buffers, textures, render targets, indexed rendering,
  depth state, rasterizer state, viewports, structured buffers, compute shaders,
  mesh loading, dynamic textures, and backbuffer capture.
- 2026-03-14 added Sound API coverage for script use and corrected several
  memory-scan/VAD documentation mismatches. If a VAD or scan signature appears
- 2026-02-12 added AngelScript GUI position/size helpers and clarified render
  callback ordering. UI overlap or ordering answers should check the current
  Render and GUI docs before assuming older behavior.
- 2026-02-01 fixed an AngelScript `hash_map` reference issue and added window
  enumeration support across supported bindings. Prefer exact API lookup before
  using these names in examples.
- 2026-02-17 added list widget operations such as get/remove/highlight/show/hide
  in the older AS-era changelog. Use the current GUI docs for exact modern
  function and method names.

## IDE, Analyzer, And Agent Tooling Signals

- 2026-04-01 added and refined IDE agent tools including terminal execution,
  user-waiting, multiple-choice prompts, and note updates. MCP/agent answers
  should still prefer this repo's `pcx-knowledge-mcp` for deterministic source
  lookup and validation.
- 2026-03-30 and 2026-04-01 describe a redesigned IDE, GitHub Models/Copilot
  integration, and expanded analyzer/reconstruction features. These are product
  capabilities, not script APIs; do not call them from Enma or AngelScript code.
- 2026-03-31 and 2026-04-06 describe analyzer memory, reconstruction, decompiler,
  and freeze/deadlock fixes. When users ask about Analyzer behavior, route them
  to `docs/perception/analyzer.md` plus changelog context rather than inventing
  scripting APIs.
- The forum notes previous AI hallucination/context-trimming fixes inside the
  Perception IDE. This repo should keep its stricter answer gate:
  `api_lookup`, `validate_code`, and `validate_answer`.

## Overlay And Client Compatibility Signals

- The 2026-05-27 overlay note says the current overlay path depends on a normal
  Discord client process being present while its overlay components are disabled.
  Treat this as compatibility guidance, not as a script API.
- The 2026-03-20 changelog says fullscreen mode became broadly supported after
  engine and overlay changes, and that overlay refresh behavior may be expected
  during client startup.
- The client self-help guide stresses loading PCX from the desktop before games
  are opened, while scripts can be loaded and unloaded in-game. This belongs in
  troubleshooting context, not code examples.
- If a user asks about overlay crashes, stream/screenshot behavior, or startup
  order, route to this file and the official client docs before answering.

## LLM Routing Implications

- For Enma tasks: load `docs/perception/llm-routing.md`,
  `docs/llms-perception-enma.md`, `docs/perception/readme.md`, and the Enma skill.
- For forum/changelog/overlay/client questions: load this file after the
  official docs. Never let this file override exact symbol signatures.
- For all code-bearing answers: finish with `pcx check-answer` or MCP
  `validate_answer` to catch hallucinated or cross-language API usage.

---

## Source: `knowledge/re-plugins-and-tools.md`

# RE Plugins & Tools Reference

IDA Pro plugins, Ghidra extensions, FLIRT signature databases, binary diffing tools, and debugger sync infrastructure for game binary reverse engineering. Every tool listed here is cloned, ready to build or install.

> This is the **plugin and tool** reference — what to install and how to use it. For kernel-specific tools (WinDbg, HyperDbg, Volatility), see `knowledge/kernel-re-tools.md`. For anti-cheat methodology, see `skill://anti-cheat-re`.

---

## IDA Pro Plugins

### hrtng — Deobfuscation & Decryption

**What:** 2024 Hex-Rays Plugin Contest winner from Kaspersky. Automated string decryption, control flow unflattening, vtable resolution for complex inheritance, and data structure recovery. The single most impactful IDA plugin for obfuscated binaries.

**Use for:** Anti-cheat driver deobfuscation, encrypted string recovery, flattened control flow restoration, complex C++ vtable resolution.

**Install:** Build from source (needs IDA SDK ≥ 7.3 + Hex-Rays decompiler). Copy the compiled `.so`/`.dll` to IDA's `plugins/` directory.

**Source:** [github.com/AandersonL/hrtng](https://github.com/AandersonL/hrtng) (Kaspersky fork)

---

### HexRaysCodeXplorer — C++ Virtual Call Analysis

**What:** Hex-Rays decompiler plugin for C++ reverse engineering. Auto-reconstructs types from vtable references, navigates virtual function calls, provides an Object Explorer window for browsing all vtables.

**Use for:** Any C++ game binary with RTTI — reconstructs class hierarchies, resolves virtual calls that IDA shows as indirect `call [rax+offset]`. Essential for Source Engine, Unreal Engine, Unity IL2CPP binaries.

**Key features:**
- Right-click in pseudocode → "Reconstruct Type" → generates C struct from vtable references
- Object Explorer → browse all vtables with class names
- Virtual call resolution → resolves `(**(code **)(*obj + 0x40))(obj)` to `CBaseEntity::Think()`

**Install:** Copy compiled plugin to IDA's `plugins/` directory.

**Source:** [github.com/REhints/HexRaysCodeXplorer](https://github.com/REhints/HexRaysCodeXplorer)

---

### ClassInformer — MSVC RTTI Scanner

**What:** Scans the binary for MSVC RTTI (Run-Time Type Information) structures — `vftable`, `type_info`, `_RTTICompleteObjectLocator`, `_RTTIClassHierarchyDescriptor`. Builds a browsable list of all C++ classes with vtables.

**Use for:** Any MSVC-compiled binary with RTTI not stripped (most game binaries, including Apex Legends, CS2, COD). First step after loading — gives you every class name the compiler embedded.

**Usage:** Edit → Plugins → Class Informer → scan. Results appear in an IDA window — sortable by name, vtable address, hierarchy depth.

**Source:** [github.com/nihilus/IDA_ClassInformer_PlugIn](https://github.com/nihilus/IDA_ClassInformer_PlugIn)

---

### SigMakerEx — Pattern Signature Generator

**What:** Generates IDA-style byte-pattern signatures from selected code. Supports multiple output formats: IDA, x64dbg, `find_code_pattern` PCX format, raw hex.

**Use for:** Generating sigs for `offsets.em` — select a unique instruction sequence, right-click → SigMaker → generate. Automatically wildcards relocatable bytes.

**Usage:** Right-click on code → SigMaker → "Create IDA Sig" or "Create Code Sig". Options: auto-wildcard, minimum uniqueness check, copy to clipboard.

**Key feature:** The "auto-wildcard" mode detects and masks RIP-relative displacements, absolute addresses, and other patch-volatile bytes — exactly what `game-cheat-guidelines` #5 (sigs over hardcodes) requires.

**Source:** [github.com/A200K/IDA-Pro-SigMaker](https://github.com/A200K/IDA-Pro-SigMaker)

---

### FIRST — Community Function Fingerprints

**What:** Cisco Talos Function Identification and Recovery Signature Tool. Free alternative to IDA's Lumina service. Matches unknown functions against a community database of identified functions using metadata hashing (not just bytes).

**Use for:** Auto-naming standard library functions, crypto routines, and common utility functions that FLIRT signatures miss. Particularly useful for statically-linked libraries where FLIRT sigs may not cover the exact version.

**Usage:** Edit → Plugins → FIRST → "Check All Functions". Functions with matches are renamed automatically. Review in FIRST's panel.

**Install:** Copy `first_plugin_ida/` content to `~/.idapro/plugins/`. Requires FIRST server access (public instance available).

**Source:** [github.com/ciscocsirt/FIRST-plugin-ida](https://github.com/ciscocsirt/FIRST-plugin-ida)

---

### RevEng.AI — Binary Similarity

**What:** AI-powered binary similarity analysis. Identifies library code, matches functions across builds/platforms, suggests function names based on training corpus. Cloud-based analysis.

**Use for:** Cross-version offset matching — when a game patches and functions move, RevEng.AI can match the old function to its new location by structural similarity rather than bytes.

**Source:** [github.com/RevEngAI/reai-ida](https://github.com/RevEngAI/reai-ida)

---

## Ghidra Plugins

### GhidrAssist — LLM-Powered RE Assistant

**What:** Integrates Claude, GPT, or local Ollama models directly into Ghidra. Explains decompiled functions, suggests names, bulk-renames symbols, answers questions about the code in context.

**Use for:** Rapid function triage on massive binaries — ask the LLM "what does this function do?" with the decompiled output as context. Bulk rename 1000+ functions in a session.

**Source:** [github.com/jtang613/GhidrAssist](https://github.com/jtang613/GhidrAssist)

---

### BinDiffHelper — Cross-Version Comparison

**What:** Integrates Google BinDiff into Ghidra's workflow. Export BinExport2 from Ghidra, diff two versions, import matched function names back.

**Use for:** Post-patch offset recovery — diff the pre-patch and post-patch binaries, identify which functions moved, import the matches to propagate names.

**Source:** [github.com/ubfx/BinDiffHelper](https://github.com/ubfx/BinDiffHelper)

---

### OOAnalyzer (Pharos) — Automated C++ Recovery

**What:** Carnegie Mellon SEI's OOAnalyzer framework for Ghidra. Automated C++ class, method, and vtable recovery using Prolog-based reasoning over the binary.

**Use for:** Large game binaries with complex C++ hierarchies where manual vtable reconstruction would take weeks. Runs as a Ghidra script and produces class definitions.

**Source:** [github.com/cmu-sei/pharos](https://github.com/cmu-sei/pharos)

---

### RevEng.AI for Ghidra

Same as the IDA plugin — AI binary similarity, function matching, and naming. Ghidra-native interface.

**Source:** [github.com/RevEngAI/reai-ghidra](https://github.com/RevEngAI/reai-ghidra)

---

## FLIRT Signature Databases

FLIRT (Fast Library Identification and Recognition Technology) signatures let IDA auto-name standard library functions. Critical for MSVC-compiled game binaries — without them, `memcpy`, `malloc`, `std::string::assign`, and thousands of CRT/STL functions appear as `sub_XXXXX`.

### Pre-Selected Signatures (51 sigs)

Priority order for game binaries compiled with MSVC v15 (Visual Studio 2017/2019):

| Signature File | What It Names | Priority |
|---|---|---|
| `libvcruntime_15_msvc_x64.sig` | CRT basics (SEH, stack guards, type info) | 1 |
| `libcmt_15_msvc_x64.sig` | C runtime (memcpy, malloc, printf, etc.) | 2 |
| `libcpmt_15_msvc_64.sig` | C++ runtime (std::string, std::vector, std::map) | 3 |
| `libcryptoMT_15_msvc_x64.sig` | OpenSSL crypto (AES, SHA, RSA) | 4 |
| `libsslMT_15_msvc_x64.sig` | OpenSSL SSL/TLS | 5 |
| `libcurl-vc-x64-*.sig` | libcurl HTTP client | 6 |
| `libboost_*.sig` | Boost (filesystem, thread, regex, etc.) | 7 |

**Apply in IDA:** `Shift+F5` → Apply new signature → select file. Apply in priority order — lower-priority sigs fill in what higher-priority ones missed.

### Signature Databases

| Database | Sigs | Coverage |
|---|---|---|
| **FLIRTDB** | 4000+ | Community collection covering MSVC, GCC, Clang, MinGW across many versions |
| **sig-database** | 2000+ | Additional collection with emphasis on game middleware (Steam API, EAC SDK, etc.) |

---

## Binary Diffing Tools

### Diaphora — IDA-Native Binary Diffing

**What:** Python-based binary diffing that runs inside IDA. Exports IDB analysis to SQLite, then diffs two exports. More accurate than BinDiff for heavily optimized/obfuscated code because it uses IDA's deeper analysis data.

**Use for:** Post-patch analysis — diff the pre-patch and post-patch game binary to find exactly what changed. Prioritize reviewing new/changed functions for updated offsets.

**Usage:**
```
# In IDA with pre-patch binary:
File → Script file → diaphora/diaphora.py → Export to SQLite

# In IDA with post-patch binary:
File → Script file → diaphora/diaphora.py → Export to SQLite

# Then: Diff the two SQLite exports
File → Script file → diaphora/diaphora.py → Diff
```

**Source:** [github.com/joxeankoret/diaphora](https://github.com/joxeankoret/diaphora)

---

### BinDiff — Structural CFG Comparison

**What:** Google's binary diffing tool. Compares control flow graphs structurally — insensitive to register allocation and instruction scheduling changes. Industry standard for cross-version binary matching.

**Use for:** Matching functions across game patches when Diaphora's byte-level diff is too noisy. BinDiff's CFG matching survives compiler flag changes and link-time optimization shuffles.

**Usage:**
```bash
# Export from IDA: File → Produce file → Create BinExport2 file
# Or from Ghidra: via BinDiffHelper extension
bindiff old_version.BinExport new_version.BinExport
# Opens BinDiff GUI with matched/unmatched function pairs
```

**Source:** [github.com/google/bindiff](https://github.com/google/bindiff)

---

## Debugger Sync — ret-sync

**What:** Real-time synchronization between a debugger and IDA/Ghidra/Binary Ninja. When you step in the debugger, the disassembler view jumps to the same address. When you set a breakpoint in IDA, it's set in the debugger.

**Supported debuggers:** WinDbg, x64dbg, GDB, LLDB, OllyDbg 1/2
**Supported disassemblers:** IDA, Ghidra, Binary Ninja

**Use for:** Live game analysis — attach x64dbg or WinDbg to the game process while IDA shows the decompiled view. Step through a function in the debugger and see the pseudocode update in real time.

**Install:**
- IDA: Copy `ext_ida/` to IDA plugins directory
- Ghidra: Install `ext_ghidra/` as a Ghidra extension
- x64dbg: Copy `ext_x64dbg/` DLL to x64dbg plugins directory
- WinDbg: Load `ext_windbg/` extension

**Source:** [github.com/bootleg/ret-sync](https://github.com/bootleg/ret-sync)

---

## SDK / Type Libraries

### r5sdk — Reversed Apex Legends SDK

**2,438 header files** reversed by the community (primarily Mauler125). Covers the entire Source Engine (Respawn fork) class hierarchy.

| Directory | Headers | Coverage |
|---|---|---|
| `game/server/` | 79 | Player, entity, AI, weapons, physics |
| `game/client/` | 35 | Client entities, HUD, viewrender |
| `game/shared/` | 15 | Player vars, weapon data, melee |
| `engine/` | 61 | Client/server engine, networking |
| `public/` | 178 | Interfaces, tier0/1/2, vscript, vgui |
| `rtech/` | 19 | Pak system, playlists, LiveAPI, Stryder |
| `networksystem/` | 6 | Pylon, bans, host manager |
| `thirdparty/` | ~300 | Boost, curl, protobuf, mbedtls, lz4, zstd |

**Import into IDA:** File → Load file → Parse C header file → select the `.h` files you need. Key starting headers: `player.h`, `baseentity.h`, `convar.h`.

**Import into Ghidra:** File → Parse C Source → add the header directories to the include path. Then apply types to decompiled functions.

**Source:** [github.com/AyeZee/r5sdk](https://github.com/AyeZee/r5sdk) (community fork)

---

## Recommended Workflow

### First Load (any game binary)

```
1. Load in IDA → let auto-analysis run
2. Apply FLIRT sigs (Shift+F5) → names CRT/STL/crypto/network functions
3. Run ClassInformer → scan RTTI → browse vtables
4. Run HexRaysCodeXplorer → reconstruct key types from vtables
5. Import SDK headers if available (r5sdk, UE SDK, etc.)
6. Run FIRST → community function fingerprints for remaining unknowns
```

### Post-Patch Update

```
1. Load new binary in IDA → apply same FLIRT sigs
2. Export both IDBs via Diaphora (or BinExport2 for BinDiff)
3. Diff → identify moved/changed functions
4. Import matched names into new IDB
5. Update offset table — re-verify sigs that moved
```

### Live Analysis

```
1. Attach debugger (x64dbg/WinDbg) to game process
2. Start ret-sync in both debugger and IDA/Ghidra
3. Set breakpoints on functions of interest
4. Step through execution → decompiler view follows in real time
5. Inspect register/memory state at each step
```

---

## MCP Integration

These tools complement the Perception MCP server's RE tools:

| Perception MCP Tool | Offline Equivalent | When to Use Which |
|---|---|---|
| `find_pattern` | SigMakerEx (generate) | SigMakerEx to create sigs; `find_pattern` to apply them live |
| `struct_dump` | ClassInformer + CodeXplorer | ClassInformer for RTTI discovery; `struct_dump` for live memory layout verification |
| `disassemble` | IDA/Ghidra decompiler | IDA for deep static analysis; `disassemble` for quick live checks |
| `analyze_vtable` | ClassInformer | ClassInformer for full hierarchy; `analyze_vtable` for live vtable state |
| `read_rtti` | ClassInformer | Same data source, different access — live vs. static |
| `generate_signature` | SigMakerEx | Both generate sigs; SigMakerEx has more options for wildcarding |
| `build_call_graph` | IDA xrefs | IDA xrefs are more complete; `build_call_graph` works on live memory |

---

## Source: `knowledge/script-organization-patterns.md`

# Script Organization Patterns

How an Enma project on Perception.cx is laid out once it grows past a single
feature. This file picks up where `templates/full-project/` stops: that scaffold
is five files and one feature; here we cover the patterns that emerge at scale —
ten or twenty features, persistent config, multiple binaries, shared utility
modules, and more than one script alive in the same session.

> **Read this before** turning the `templates/full-project/` scaffold into a real
> multi-feature project. The five-file layout is the *starting point*; everything
> below extends it without re-architecting it. If you are writing a single
> overlay, stop at the scaffold — none of this earns its keep yet.

The one rule the whole toolkit agrees on (`game-cheat-guidelines` #6, *one
feature, one file*) is the floor, not the ceiling. The hard questions start the
moment two features want the same offset, the same `world_to_screen`, or the same
config file. This is the decision guide for those questions.

---

## The 5-file baseline (review)

The scaffold in `templates/full-project/` is the smallest layout that already
honors the guidelines. Five files, one direction of dependency, one bundle order:

```
templates/full-project/
├── globals.em   # proc_t, module base/size, config bound to GUI
├── offsets.em   # named sigs + RIP-relative resolver (imports globals)
├── feature.em   # one feature: update reads, render draws (imports globals, offsets)
├── menu.em      # GUI sidebar + config save/load (imports globals)
└── main.em      # main(): attach, resolve, setup_menu, register routines
```

Bundle order is the dependency order: `globals → offsets → feature → menu →
main`. Nothing imports `main`; `globals` imports nothing project-local. Every
other file reaches *down* toward `globals`, never sideways into a sibling
feature. Keep that arrow pointing one way and the project stays reloadable.

Everything in this document is a way of adding files to that picture *without*
breaking the arrow. When a new pattern tempts you to make `feature_a.em` import
`feature_b.em`, that is the signal that the shared thing belongs in `globals.em`
or a new utility module — not in a sibling.

---

## Shared state: what goes where

**`globals.em` holds state every feature reads. A feature's own tuning lives in
the feature file.** The test: if exactly one feature cares about a variable, it
is not global.

Cross-feature state — the process handle, the module base/size, the resolved
entity-list pointer, a per-tick entity cache — belongs in `globals.em` because
ESP, radar, and aimbot all read the same entities and you walk that list once
(rule #4, separate scan from render; rule #6, don't duplicate reads). Per-feature
tuning — ESP box thickness, aimbot smoothing, radar zoom — belongs to the feature
that owns it, bound to that feature's own GUI section (rule #11).

```cpp
// globals.em — cross-feature state ONLY
import "vec";

proc_t g_proc;
uint64 g_base = 0;            // uint64 always (rule #2)
uint64 g_size = 0;
uint64 g_entity_list = 0;     // resolved once, read by every feature
bool   g_initialized = false;

// One shared entity cache, filled by a single walk in a shared update routine.
array<uint64> g_entities;     // valid entity bases this tick
array<vec3>   g_positions;    // world positions, parallel to g_entities
```

```cpp
// esp.em — this feature's tuning is private to this file
import "vec";
import "color";
import "globals";

bool    g_esp_enabled  = true;   // ESP owns these, not globals.em
float64 g_esp_distance = 3000.0;
color   g_esp_color    = color(80, 170, 255, 220);

void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;
    color box = color(80, 170, 255, 220);   // construct per frame (rule #7)
    for (int32 i = 0; i < g_positions.length(); i++) {
        // draw from the shared cache — esp.em never walks the list itself
    }
}
```

**Anti-pattern: a feature writing into another feature's variables.** If `aim.em`
flips `g_esp_color` to flag its current target, you now have two files that can
change one variable and a hot-reload of either that desyncs the other.

```cpp
// WRONG — aim.em reaches into esp.em's state
g_esp_color = color(255, 0, 0, 255);   // "highlight the aim target"

// RIGHT — shared intent goes through globals.em, each feature reads it
// globals.em:  uint64 g_aim_target = 0;
// aim.em:      g_aim_target = best;          // aim owns the write
// esp.em:      if (g_entities[i] == g_aim_target) box = color(255,0,0,255);  // esp owns the read
```

The rule: **a global has exactly one writer.** Many readers are fine; two writers
is a bug waiting for a patch day.

---

## Offset modules: one per binary, not one per feature

**Sigs are grouped by the binary they scan, never by the feature that consumes
them.** Almost every project targets one module and `offsets.em` is enough. The
pattern only branches when you legitimately read two binaries — a game plus its
anti-cheat-adjacent helper DLL, or a launcher plus the game.

```
offsets-game.em      # sigs scanned in game.exe
offsets-engine.em    # sigs scanned in engine.dll
```

Each offset module owns its own base/size and resolves against it; a feature
imports whichever module holds the sig it needs.

```cpp
// offsets-game.em — sigs for game.exe (cite each, rule #1 / #5)
import "globals";

// CEntityList global — LEA RCX, [rip+????]   (sig from IDA, not a hardcode)
const string SIG_ENTITY_LIST = "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 8B D8";

bool resolve_game() {
    uint64 hit = g_proc.find_code_pattern(g_base, g_size, SIG_ENTITY_LIST);
    if (hit == 0) { println("[offsets-game] SIG_ENTITY_LIST stale"); return false; }
    int32 disp = g_proc.r32(hit + 3);                       // RIP-relative, 4 bytes
    g_entity_list = hit + 7 + cast<uint64>(disp);           // end-of-insn + disp
    return g_entity_list != 0;                              // validate (rule #3)
}
```

**The hard rule: a signature is defined exactly once.** The moment the same byte
pattern appears in two feature files, a patch breaks one copy and not the other,
and you debug a "half-working" cheat. If two features need `SIG_ENTITY_LIST`,
both import the offset module — they never re-declare the constant.

```
// WRONG: SIG_ENTITY_LIST pasted into both esp.em and radar.em
// RIGHT: declared in offsets-game.em; esp.em and radar.em both `import "offsets-game";`
```

---

## Config persistence pattern

**Serialize GUI state to a JSON file with the JSON addon, load it in `main()`
before building the menu, and save it on an explicit trigger.** There is no
unload callback to hook — see the lifecycle note below — so saving is something
*you* invoke, not something the host does for you.

Load first so widgets come up showing the saved values; the scaffold's
`setup_menu()` already calls `load_config()` at its top. Use the documented
filesystem API (`fs_read_file` / `fs_write_file` / `fs_file_exists`, all gated by
`file_system_access`) and the JSON addon (`json_parse`, `json_object`,
`.set_key` / `.get_key`, `.stringify()` / `.pretty()`).

```cpp
// menu.em — JSON config persistence
import "globals";

const string CFG_PATH = "configs/active.json";

void save_config() {
    json_value root = json_object();
    root.set_key("enabled",      json_parse(to_string(g_esp_enabled)));
    root.set_key("max_distance", json_parse(to_string(g_esp_distance)));
    root.set_key("hotkey",       json_parse(to_string(g_aim_hotkey)));

    if (!fs_dir_exists("configs")) fs_create_directory("configs");
    if (!fs_write_file(CFG_PATH, root.pretty()))     // pretty() so it's hand-editable
        println("[cfg] save failed — check file_system_access permission");
}

void load_config() {
    if (!fs_file_exists(CFG_PATH)) return;           // first run: keep defaults
    json_value root = json_parse(fs_read_file(CFG_PATH));
    if (!root.is_valid()) { println("[cfg] corrupt, using defaults"); return; }

    if (root.has_key("enabled"))      g_esp_enabled  = root.get_key("enabled").as_bool();
    if (root.has_key("max_distance")) g_esp_distance = root.get_key("max_distance").as_num();
    if (root.has_key("hotkey"))       g_aim_hotkey   = cast<int32>(root.get_key("hotkey").as_int());
}
```

`json_parse` returns an invalid value (not a throw) on malformed input, so the
`is_valid()` guard is the whole error path — a truncated or hand-broken config
falls back to defaults instead of taking the script down. `has_key` before
`get_key` means a config written by an older build (missing a field you added
later) loads cleanly: unknown-to-old and missing-from-new both degrade to the
default. That forward/backward tolerance is the reason to prefer JSON objects over
the positional `key=value` text format the scaffold ships with.

**Lifecycle reality — there is no `on_unload` hook.** Per
`docs/perception/lifecycle-and-routines.md`, a script unloads when `main()`
returns `<= 0`, when the user unloads it, or when the host shuts down; routines
simply stop and render resources are freed automatically. Nothing runs *your*
code on the way out. So persistence is triggered one of three ways:

- **Save button** — `section_button(sec, "Save Config", cast<int64>(save_config))`.
  Explicit, zero overhead, what the scaffold uses.
- **Save hotkey** — check `key_fired(g_save_key)` in a routine, call
  `save_config()` on the edge. Convenient mid-game.
- **Autosave on change** — diff GUI state in the update routine and save when it
  moves. Simplest to reason about, but it writes to disk during gameplay; gate it
  behind a debounce so a slider drag isn't a hundred file writes.

```cpp
// defer: explicit Save button only. Autosave-on-change when users complain
//        about losing edits; debounce it so a slider drag isn't N disk writes.
```

---

## Multi-script coordination

Sometimes you want two scripts loaded in the same PCX session — a stable "base"
script you trust, plus a "wip" experimental overlay you reload constantly without
risking the base. The question is whether they can share state, and the honest
answer is *mostly no, and that's usually fine*.

The scripting layer exposes **no IPC primitive** — no named pipes, no shared
memory between scripts. Do not invent one. The filesystem is **sandboxed to a
per-script data root** (`docs/perception/filesystem-api.md`), so a file written
by script A is not guaranteed visible to script B; treat cross-script file
sharing as unsupported unless you have verified on your install that both scripts
resolve to the same root. That leaves three real options:

| Approach | How | When it's worth it |
| --- | --- | --- |
| **Don't share** (default) | Each script attaches its own `proc_t`, resolves its own offsets, walks its own list | Almost always. Duplicate reads are cheap next to the simplicity |
| **Shared file** | One script writes `state/shared.json`, the other polls it | Only if both resolve to the same sandbox root *and* the data is slow-changing (resolved offsets, target id) |
| **Single script, two modules** | Collapse both into one script; the "experimental" part is just another feature file you hot-reload | When you actually need shared live state — this is the supported way to get it |

**The tradeoff is duplicate reads vs. coupling.** Two independent scripts each
walking the entity list costs you two walks per tick — measurable only if the
list is huge. Sharing state via a file couples their reload cycles and adds a
parse on every poll. The "single script, two feature modules" path gives you true
shared state for free (it's just `globals.em` again) at the cost of the isolation
you wanted in the first place. Pick duplication unless a profiler says otherwise.

```cpp
// defer: two independent scripts, duplicate entity walks accepted.
//        Merge into one script with shared globals.em if the double walk
//        shows up in the frame budget.
```

---

## Utility modules: when extraction pays off

**`world_to_screen` lives in exactly one place. So does the pattern-scan
resolver. So does the bone-matrix unpacker.** A second copy of W2S is a second
place to get the behind-camera check wrong (rule #10).

The extraction heuristic is a counting rule, straight from
`pcx-coding-discipline` #5 (*deletion before addition*):

- **3+ features need it → utility module.** Extract to `util-math.em` (or
  `util-mem.em`) and import it everywhere. The shared definition is now the only
  one to fix after a patch.
- **Exactly 2 features need it → leave it duplicated.** Two copies you can see is
  cheaper to reason about than one indirection you have to chase, and the second
  caller is not yet proof the abstraction is right.
- **1 feature needs it → inline it.** A wrapper with one caller adds a name, not
  value. Inline the body.

```cpp
// util-math.em — shared because esp, radar, AND aim all project to screen (3 callers)
import "vec";
import "globals";

bool world_to_screen(vec3 world, out vec2 screen) {
    uint64 m = g_view_matrix;                       // resolved in globals/offsets
    float64 w = g_proc.rf32(m + 12) * world.x
              + g_proc.rf32(m + 28) * world.y
              + g_proc.rf32(m + 44) * world.z
              + g_proc.rf32(m + 60);
    if (w < 0.001) return false;                    // behind camera (rule #10)
    float64 inv = 1.0 / w;
    float64 nx = (g_proc.rf32(m + 0)  * world.x + g_proc.rf32(m + 16) * world.y
                + g_proc.rf32(m + 32) * world.z + g_proc.rf32(m + 48)) * inv;
    float64 ny = (g_proc.rf32(m + 4)  * world.x + g_proc.rf32(m + 20) * world.y
                + g_proc.rf32(m + 36) * world.z + g_proc.rf32(m + 52)) * inv;
    float64 vw = get_view_width();
    float64 vh = get_view_height();
    screen = vec2((vw * 0.5) + (nx * vw * 0.5), (vh * 0.5) - (ny * vh * 0.5));
    return true;
}
```

```cpp
// WRONG — esp.em and radar.em each carry their own W2S; one gets the w-check
//         fixed after a patch, the other still mirrors points behind the camera.
// RIGHT — both `import "util-math";` and call world_to_screen(); one definition.
```

Resist extracting too early. A `util-mem.em` that wraps `g_proc.ru64` in
`read_ptr()` is the one-caller mistake even when three features call it — the
`proc_t` API *is* the interface (rule from `pcx-coding-discipline` #5). Extract
behavior with real logic (W2S, the RIP resolver, bone unpacking), not one-line
passthroughs.

---

## Feature toggles in `main()` vs the feature module

**Two different switches, two different homes.** Conflating them is why a feature
"won't turn off" or "won't turn on."

- **Load switch — does the feature exist at all this session?** Lives in
  `main()`, as whether you call `register_routine` for it. An unregistered
  feature costs zero per frame; its file can even be absent from the bundle.
- **Runtime switch — is the loaded feature drawing right now?** Lives in the
  feature's own GUI checkbox, read at the top of its routine.

```cpp
// main.em — LOAD switch: register or don't. Comment out the line to drop a feature.
int64 main() {
    // ... attach, resolve ...
    setup_menu();
    register_routine(cast<int64>(esp_update),   0);
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // aim left out this build
    g_initialized = true;
    return 1;
}
```

```cpp
// esp.em — RUNTIME switch: the registered routine early-outs when the box is off.
void esp_render(int64 data) {
    if (!g_esp_enabled || !g_initialized) return;     // GUI checkbox (rule #11)
    // ... draw ...
}
```

**Why both:** the load switch is your kill switch — a feature you suspect is
crashing or detectable, you drop by deleting one `register_routine` line and
reloading, with no per-frame cost and no risk it runs. The runtime switch is the
user-facing toggle for a feature you trust enough to ship. A feature with only a
runtime toggle still executes its early-out every frame even when "off"; a
feature with only a load switch can't be turned off without a reload. You want
both levers.

---

## Module-version pinning

**A feature that depends on a specific shape of `globals.em` says so at the top of
its file.** When you change a shared structure, this comment is the list of files
to revisit — Enma won't warn you that `feature.em` expected the old layout, it
will just read the wrong field.

The pattern is a `// requires:` line naming the shared contract the feature was
written against:

```cpp
// radar.em
// requires: globals v2  (g_entities as flat array<uint64>, g_positions parallel)
import "globals";

void radar_render(int64 data) {
    for (int32 i = 0; i < g_positions.length(); i++) {
        // assumes g_positions[i] pairs with g_entities[i] — the v2 contract
    }
}
```

When you bump `globals.em` — say you replace the two parallel arrays with a single
`array<entity_t>` — grep for `requires: globals v2` and every file that needs
updating is named for you. Bump the version in `globals.em`'s header comment and
update each `requires:` as you migrate it:

```cpp
// globals.em
// version: v3  (g_entities is now array<entity_t>; v2 parallel arrays removed)
```

This is documentation, not a runtime check — there is no module-version assert in
the language. Its whole value is that the next reader (often you, post-patch) sees
the dependency without reverse-engineering it. Keep the line honest or delete it;
a stale `requires:` is worse than none.

---

## Dead-code elimination

**A feature you stopped using: drop it from the bundle order, comment out its
`register_routine`, rename the file so it's visibly inactive — but keep it in the
tree.** Don't `git rm` it.

The reasoning is specific to this domain. A feature file is a worked record of a
sig, a struct layout, and the math that turned them into an overlay — knowledge
that took an IDA session to produce. After a patch the *code* is stale but the
*structure* is still the fastest way back: you re-sig, re-verify the offsets, and
the feature is alive again. Git-deleting it buries that record in history where
future-you won't think to look.

The compromise that keeps it from rotting silently: **rename to
`feature-dead-<name>.em`** so it's unmistakably inactive at a glance, and remove
its routine registration so nothing runs it.

```cpp
// main.em
import "esp";
import "radar";
// import "feature-dead-aim";   // parked: offsets stale since the season patch

int64 main() {
    register_routine(cast<int64>(esp_render),   0);
    register_routine(cast<int64>(radar_render), 0);
    // register_routine(cast<int64>(aim_update), 0);   // dead: see feature-dead-aim.em
    return 1;
}
```

```
project/
├── esp.em
├── radar.em
└── feature-dead-aim.em    # inactive, kept as a re-sig starting point
```

The `dead-` prefix is the signal to every tool and reader that this file is not
in the build. When you revive it, rename back to `aim.em`, re-verify the sigs
against the live binary (`game-cheat-guidelines` #12), and re-add the
registration.

---

## The shape of a 20-feature project

A project with many features, two target binaries, and shared utilities still
keeps the one-way dependency arrow from the scaffold — it just has more files at
each layer. Features depend on utils and offsets; utils and offsets depend on
globals; nothing depends on a sibling feature.

```
project/
├── globals.em             # version: v3 — proc_t, bases, shared entity cache
│
├── offsets-game.em        # sigs scanned in game.exe
├── offsets-engine.em      # sigs scanned in engine.dll
│
├── util-math.em           # world_to_screen, angle math   (3+ callers)
├── util-mem.em            # RIP resolver, bone-matrix unpack (3+ callers)
│
├── esp.em                 # requires: globals v3
├── radar.em               # requires: globals v3
├── glow.em                # requires: globals v3
├── aim.em                 # requires: globals v3, offsets-game
├── triggerbot.em          # requires: globals v3, offsets-game
├── nospread.em            # requires: globals v3, offsets-engine
├── loot-esp.em            # requires: globals v3, offsets-game
├── spectator-list.em      # requires: globals v3, offsets-engine
├── ...                    # (more features, each one file)
├── feature-dead-bhop.em   # parked: re-sig after patch
│
├── menu.em                # GUI sections + JSON config persistence
└── main.em                # attach, resolve_game/resolve_engine, register all
```

Dependency direction, top to bottom:

```
  main.em  ──registers──>  every feature
     │
  menu.em  ──reads/writes──>  each feature's config + globals
     │
  esp / radar / aim / ...  ──import──>  util-math, util-mem, offsets-*
     │
  util-*, offsets-*  ──import──>  globals.em
     │
  globals.em  ──imports──>  vec, color   (engine modules only)
```

`main()` grows linearly: resolve each binary, then one `register_routine` per
active feature. `menu.em` grows one `create_section` per feature. Everything else
stays a single file you can reload in isolation — which is the entire point of the
split, and the reason a 20-feature project is still tractable when a single
2000-line `cheat.em` would not be.

---

## Anti-Patterns

A flat list of organizational mistakes and the consequence each one buys you:

- **Monolithic `cheat.em`** — every feature in one file; a hot-reload to fix one
  box re-runs and can break all twenty. Split per feature (#6).
- **Duplicate sig definitions** — the same byte pattern declared in two feature
  files; a patch breaks one copy, you ship a half-working cheat. One sig, one
  module.
- **Features mutating each other's state** — two writers on one global; reload
  either and they desync. One writer per global, many readers.
- **`feature_a.em` importing `feature_b.em`** — sideways dependency; now neither
  reloads cleanly. Shared things go down into `globals.em` or a util module.
- **GUI widgets created in an update/render loop** — `create_section` /
  `section_checkbox` belong in `setup_menu()` run once, not per frame. Per-frame
  widget creation duplicates state and tanks the frame budget (#11).
- **Reading widget state deep inside nested loops** — read the toggle once at the
  top of the routine, then branch; don't re-read per entity.
- **Per-binary offset files split by feature instead** — `esp-offsets.em` +
  `radar-offsets.em` for the same game.exe re-declares shared sigs. Group offsets
  by binary, not by consumer.
- **Caching colors/vecs in globals "to avoid allocation"** — they're stack value
  types; the global only adds mutable state. Construct per frame (#7).
- **One-caller utility wrappers** — `read_ptr()` around a single `g_proc.ru64`
  adds a name, not value. Inline until 3 callers earn the extraction.
- **Config saved on a nonexistent unload hook** — there is no `on_unload`; the
  save never fires. Trigger saves from a button, hotkey, or debounced autosave.
- **Git-deleting a patched-out feature** — buries the sig/struct knowledge in
  history. Rename to `feature-dead-<name>.em` and keep it.
- **Stale `requires:` comments** — a version pin that no longer matches
  `globals.em` misleads the next reader. Keep it honest or remove it.

---

## See Also

- `templates/full-project/` — the five-file scaffold this document extends;
  start there, grow into these patterns.
- `.claude/skills/game-cheat-guidelines/SKILL.md` — the code-shape rules every
  block here honors, especially #1 (ground offsets), #6 (one feature per file),
  and #11 (GUI for tunables).
- `.claude/skills/pcx-coding-discipline/SKILL.md` — the process layer: #5
  (deletion before addition) is the source of the utility-extraction counting
  rule.
- `knowledge/common-patterns.md` — the per-feature building blocks (W2S, entity
  iteration, config) these layouts arrange.
- `docs/enma/lang-modules.md` — the `import` / module-resolution mechanics behind
  the dependency arrow.
- `docs/enma/addon-json.md` and `docs/perception/filesystem-api.md` — the real
  JSON and sandboxed-filesystem APIs used by the config-persistence pattern.
- `docs/perception/lifecycle-and-routines.md` — why there is no unload hook and
  how `register_routine` makes the load switch.

---

## Source: `knowledge/vmprotect2-analysis.md`

# VMProtect 2.x Analysis with vmp2

Practical guide for analyzing binaries protected by **VMProtect 2.x** using the
open-source **backengineering/vmp2** toolchain, x64dbg VMProtect/ScyllaHide
plugins, and the `tools/analyze-vmprotect.py` toolkit helper.

> **Scope:** Authorized security research only. Use these tools on binaries you
> own, have explicit permission to test, or are analyzing in a controlled CTF /
> research environment. See `skill://authorized-security-research`.

---

## What is VMProtect 2.x?

VMProtect 2.x virtualizes selected functions by translating x86/x64 machine code
into a custom bytecode executed by a runtime interpreter (the *VM dispatcher*).
Key artifacts:

- **`.vmp0` / `.vmp1` / `.vmp2`** sections containing VM bytecode and metadata.
- **VM entry stubs** at every protected function that push a key/bytecode
  pointer, then `call` or `jmp` into `vmenter`.
- **A dispatch loop** that reads an opcode, decrypts it with a rolling key,
  and jumps through a handler table.
- **Import protection**: each API call is redirected through a small stub that
  resolves at runtime.
- **Anti-debug layer**: `RDTSC`, `INT 2D`, `CPUID`, PEB checks, and
  `NtQueryInformationProcess`/`NtSetInformationThread` tricks.

The `backengineering/vmp2` suite (C++, LLVM/Qt/Unicorn) automates the heavy
lifting:

| Component | Purpose |
|-----------|---------|
| `vmemu` | Unpacks VMP-protected binaries by emulating execution until OEP. |
| `vmdevirt` | Lifts VMP bytecode to a closer-to-native representation (experimental). |
| `vmprofiler` | Profiles and visualizes VM handler coverage. |
| `vmprofiler-cli` | Command-line access to `vmprofiler` analysis. |
| `vmhook` | Hooks VM entry stubs to capture bytecode streams at runtime. |
| `vmassembler` | Assembler/disassembler for VMP bytecode research. |

Source: [github.com/backengineering/vmp2](https://github.com/backengineering/vmp2)

---

## Triage with `tools/analyze-vmprotect.py`

The toolkit ships a stdlib-only Python script that detects VMP artifacts,
suggests a tooling chain, and (optionally) shells out to an external `vmemu`
binary for unpacking.

```bash
# Basic analysis (read-only)
python3 tools/analyze-vmprotect.py target.exe

# JSON output for further automation
python3 tools/analyze-vmprotect.py --json target.exe

# Optional: invoke external vmemu to dump unpacked memory
python3 tools/analyze-vmprotect.py --run-vmemu --out unpacked.bin target.exe
```

The script reports:

- VMP section presence and per-section entropy.
- Estimated VMP version/variant.
- VM entry stubs (`PUSH imm32; CALL/JMP rel32`).
- Anti-debug indicators (`RDTSC`, `INT 2D`, PEB debug checks, `CPUID`).
- Tool recommendations (`vmp2`, `x64dbg+ScyllaHide`, `NoVmp`, `VTIL-Core`).

---

## Workflow: VMP 2.x → Unpacked → Devirtualized

### 1. Identify the Protector

Check sections and strings:

```bash
r2 -nn target.exe
iS
iz~vmp|VMProtect|protect
```

Or use the toolkit script:

```bash
python3 tools/analyze-vmprotect.py --json target.exe | jq '.vmprotect_detected, .version_hint'
```

### 2. Bypass Anti-Debug (Live Debugging)

Use x64dbg with the ScyllaHide plugin:

1. Load target in x64dbg.
2. Plugins → ScyllaHide → Options → check **all** anti-debug bypasses.
3. Set breakpoints on `VirtualProtect` and `NtSetInformationThread`.
4. Run; when `VirtualProtect` hits a large `PAGE_EXECUTE_READ` region on the
   original `.text`, the protector has decrypted/unpacked code.
5. Record the OEP and dump the process with Scylla.

### 3. Unpack with `vmemu`

If you have a legitimately obtained `vmemu` binary:

```bash
vmemu --bin target.exe --unpack --out unpacked.bin
```

This emulates the VMP runtime until the original entry point is reached and
writes a dumped memory image. The toolkit wrapper can do this for you:

```bash
python3 tools/analyze-vmprotect.py --run-vmemu --out unpacked.bin target.exe
```

### 4. Find VM Bytecode Regions and Handlers

After unpacking, locate the `.vmp2` bytecode and the dispatcher:

```bash
r2 -nn unpacked.bin
s section..vmp2
px 256             # inspect first bytes
/V 0f b6 00        # search for dispatcher fetch: movzx eax, byte [rax]
```

Typical dispatcher shape:

```asm
movzx   eax, byte ptr [rcx]      ; fetch next opcode
xor     al, <key_byte>            ; decrypt
and     eax, 0xff
mov     rdx, [handler_table]
jmp     qword ptr [rdx + rax*8]  ; dispatch
```

### 5. Lift / Devirtualize

For VMP 2.x, try `vmdevirt` first:

```bash
vmdevirt --input target.exe --bytecode-rva 0x12345 --output lifted.asm
```

For VMP 3.x, prefer `NoVmp` / `VTIL-Core`:

```bash
novmp --input target.exe --rva 0x12345 --output lifted.ll
opt -O2 lifted.ll -o optimized.ll
```

### 6. Validate the Output

- Compare lifted code against known native implementations of the same logic.
- Re-run in a debugger and ensure function outputs match the original.
- Look for missing side effects (VMP sometimes hides IAT writes or SEH setup).

---

## x64dbg VMProtect Plugin Workflow

Some researchers use a dedicated x64dbg VMProtect plugin to speed up VMP work:

1. **Install** the plugin into `x64dbg\x64\plugins`.
2. **Enable ScyllaHide** to neutralize anti-debug.
3. **Plugins → VMProtect → Trace VM entry** to log every `vmenter` call.
4. **Dump bytecode** to a file for offline analysis with `vmassembler` or
   `vmprofiler-cli`.
5. **Set conditional breakpoints** on handler transitions to capture execution
   traces.

> The plugin interface is tool-specific; refer to its documentation for exact
> menu names. The principle remains: bypass anti-debug → trace VM entries → dump
> bytecode → lift/decode.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `vmemu` fails immediately | Anti-debug is still active; use ScyllaHide or HyperDbg. |
| Dispatcher not found | VMP version may be 3.x; switch to `NoVmp` / `VTIL-Core`. |
| Lifted output is incomplete | Provide the exact bytecode RVA and ensure the binary is unpacked first. |
| Imports still broken after dump | Reconstruct IAT with Scylla before saving the final executable. |
| Entropy low in `.vmp2` | The section may be uninitialized/padded, or the binary is packed differently. |

---

## Tool Matrix

| Goal | Best Tool | Notes |
|------|-----------|-------|
| Detect / triage VMP | `tools/analyze-vmprotect.py` | Stdlib-only, safe, fast. |
| Unpack VMP 2.x | `vmemu` (vmp2) | Requires built `vmp2` suite. |
| Live anti-debug bypass | `x64dbg + ScyllaHide` | Easiest first step. |
| Devirtualize VMP 3.x | `NoVmp` / `VTIL-Core` | Static lifting to LLVM/VTIL IR. |
| VM handler profiling | `vmprofiler` / `vmprofiler-cli` | Coverage and handler statistics. |
| Bytecode disassembly | `vmassembler` | VMP-specific opcodes. |

---

## See Also

- `signatures/obfuscation/protector-patterns.md` — byte patterns for VMP entry, dispatcher, import stubs.
- `knowledge/deobfuscation-tools.md` — broader deobfuscation tool reference.
- `.claude/skills/deobfuscation/SKILL.md` — general deobfuscation methodology.
- `skill://authorized-security-research` — legal/ethical scope.
