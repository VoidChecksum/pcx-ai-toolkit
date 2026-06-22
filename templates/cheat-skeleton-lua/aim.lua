-- aim.lua — smooth aimbot with FOV filter

-- Engine-specific helpers — replace with your target's angle read/write.
function read_view_angles()
    -- placeholder: read from your engine's view-angle address
    return {x=0, y=0}
end

function write_view_angles(angles)
    -- placeholder: clamp pitch to [-89, 89] and write to engine memory
end

function aimbot_update()
    if not g_aim_enabled or not g_initialized or not g_proc or not g_proc:alive() then return end
    if not is_key_down(g_aim_key) then
        g_aim_target.valid = false
        return
    end

    local local_pos = read_vec3(g_local_player + OFF_POS)
    local current   = read_view_angles()

    local best = { valid=false, ptr=0, health=0, team=0, pos={x=0,y=0,z=0}, head={x=0,y=0,z=0} }
    local best_score = 1e9

    for i = 1, MAX_ENTITIES do
        local e = g_entities[i]
        if not e.valid or e.team == g_local_team or e.health <= 0 then goto continue end
        if not in_fov(local_pos, current, e.head, g_aim_fov) then goto continue end

        local target_ang = calc_angle(local_pos, e.head)
        local yaw_delta   = normalize_delta(target_ang.y - current.y)
        local pitch_delta = math.max(-89.0, math.min(89.0, target_ang.x - current.x))
        local score = yaw_delta*yaw_delta + pitch_delta*pitch_delta

        if score < best_score then
            best_score = score
            best = {
                valid = e.valid,
                ptr   = e.ptr,
                health= e.health,
                team  = e.team,
                pos   = {x=e.pos.x, y=e.pos.y, z=e.pos.z},
                head  = {x=e.head.x, y=e.head.y, z=e.head.z}
            }
        end
        ::continue::
    end

    g_aim_target = best
end

function aimbot_render()
    if not g_aim_enabled or not g_aim_target.valid then return end

    local local_pos = read_vec3(g_local_player + OFF_POS)
    local target = calc_angle(local_pos, g_aim_target.head)
    local current = read_view_angles()

    local yaw_delta   = normalize_delta(target.y - current.y)
    local pitch_delta = math.max(-89.0, math.min(89.0, target.x - current.x))

    local smoothed = {
        x = current.x + pitch_delta * g_aim_smooth,
        y = current.y + yaw_delta   * g_aim_smooth
    }

    write_view_angles(smoothed)
end
