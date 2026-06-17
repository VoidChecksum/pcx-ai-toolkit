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
