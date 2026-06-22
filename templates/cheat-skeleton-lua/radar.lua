-- radar.lua — 2D world radar

RADAR_SCALE  = 0.05
RADAR_RADIUS = 100.0

function world_to_map(world)
    return { x = world.x, y = world.y }
end

function radar_render()
    if not g_radar_enabled or g_esp_count == 0 then return end

    local local_pos = read_vec3(g_local_player + OFF_POS)
    local local2d = world_to_map(local_pos)

    local vw, vh = get_view()
    local cx = vw - 150.0
    local cy = vh - 150.0

    draw_rect_filled(cx - RADAR_RADIUS, cy - RADAR_RADIUS,
                     RADAR_RADIUS*2, RADAR_RADIUS*2,
                     0, 0, 0, 160,
                     8.0, 0)

    draw_circle(cx, cy, 4.0,
                255, 255, 255, 255,
                1.0, true)

    for i = 1, MAX_ENTITIES do
        local e = g_entities[i]
        if not e.valid then goto continue end

        local blip = world_to_map(e.pos)
        local rel = { x = blip.x - local2d.x, y = blip.y - local2d.y }
        rel.x = rel.x * RADAR_SCALE
        rel.y = rel.y * RADAR_SCALE

        if rel.x*rel.x + rel.y*rel.y > RADAR_RADIUS*RADAR_RADIUS then goto continue end

        local r, g_, b = 255, 80, 80
        if e.team == g_local_team and g_local_team ~= 0 then
            r, g_, b = 80, 255, 80
        end

        draw_circle(cx + rel.x, cy + rel.y, 4.0,
                    r, g_, b, 255,
                    1.0, true)
        ::continue::
    end
end
