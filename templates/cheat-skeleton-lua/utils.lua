-- utils.lua — W2S, distance, team helpers

PI       = 3.14159265358979323846
RAD2DEG  = 180.0 / PI
DEG2RAD  = PI / 180.0

-- Read a 3-float vector from a memory address.
function read_vec3(addr)
    if addr == 0 then return {x=0, y=0, z=0} end
    local x = g_proc:rf32(addr + 0)
    local y = g_proc:rf32(addr + 4)
    local z = g_proc:rf32(addr + 8)
    return {x=x, y=y, z=z}
end

-- Pointer-chain reader.
function read_chain(base, offsets)
    local addr = base
    for _, off in ipairs(offsets) do
        if addr == 0 then return 0 end
        addr = g_proc:ru64(addr)
        if addr == 0 then return 0 end
        addr = addr + off
    end
    return addr
end

function distance3d(a, b)
    local dx = a.x - b.x
    local dy = a.y - b.y
    local dz = a.z - b.z
    return math.sqrt(dx*dx + dy*dy + dz*dz)
end

function world_to_screen(world)
    if g_view_matrix == 0 then return nil end

    local m = {}
    for i = 0, 15 do
        m[i] = g_proc:rf32(g_view_matrix + i * 4)
    end

    local w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15]
    if w < 0.001 then return nil end

    local inv_w = 1.0 / w
    local nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w
    local ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w

    local vw, vh = get_view()
    return {
        x = (vw * 0.5) + (nx * vw * 0.5),
        y = (vh * 0.5) - (ny * vh * 0.5)
    }
end

function calc_angle(src, dst)
    local d = { x = dst.x - src.x, y = dst.y - src.y, z = dst.z - src.z }
    local dist_xy = math.sqrt(d.x*d.x + d.y*d.y)
    local pitch = math.atan(-d.z, dist_xy) * RAD2DEG
    local yaw   = math.atan(d.y, d.x) * RAD2DEG
    return {x=pitch, y=yaw}
end

function normalize_delta(delta)
    return (delta + 540.0) % 360.0 - 180.0
end

function angles_to_forward(pitch_deg, yaw_deg)
    local p = pitch_deg * DEG2RAD
    local y = yaw_deg   * DEG2RAD
    local cp = math.cos(p)
    return {
        x = cp * math.cos(y),
        y = cp * math.sin(y),
        z = -math.sin(p)
    }
end

function in_fov(src, view_angles, target, fov_deg)
    local dir = { x = target.x - src.x, y = target.y - src.y, z = target.z - src.z }
    local len = math.sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z)
    if len == 0.0 then return false end
    dir = { x = dir.x/len, y = dir.y/len, z = dir.z/len }

    local fwd = angles_to_forward(view_angles.x, view_angles.y)
    local dot = fwd.x*dir.x + fwd.y*dir.y + fwd.z*dir.z
    return dot >= math.cos(fov_deg * DEG2RAD)
end
