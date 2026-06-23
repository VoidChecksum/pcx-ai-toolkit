-- esp.lua — box ESP, snaplines, health text

PLAYER_HEIGHT = 72.0

function esp_update()
    if not g_esp_enabled or not g_initialized or not g_proc or not g_proc:alive() then return end

    g_esp_count = 0

    if g_local_player ~= 0 then
        g_local_team = g_proc:r32(g_local_player + OFF_TEAM)
    end

    for i = 1, MAX_ENTITIES do
        local ent = g_proc:ru64(g_entity_list + (i - 1) * 8)
        if ent == 0 then goto continue end
        if ent == g_local_player then goto continue end

        local health = g_proc:r32(ent + OFF_HEALTH)
        if health <= 0 or health > 999 then goto continue end

        local info = g_entities[i]
        info.ptr    = ent
        info.health = health
        info.team   = g_proc:r32(ent + OFF_TEAM)
        info.pos    = read_vec3(ent + OFF_POS)
        info.head   = { x = info.pos.x, y = info.pos.y, z = info.pos.z + PLAYER_HEIGHT }
        info.valid  = true

        g_esp_count = g_esp_count + 1
        if g_esp_count >= MAX_ENTITIES then break end
        ::continue::
    end
end

function esp_render()
    if not g_esp_enabled or g_esp_count == 0 then return end

    local vw, vh = get_view()
    local screen_bottom = { x = vw * 0.5, y = vh }

    for i = 1, MAX_ENTITIES do
        local e = g_entities[i]
        if not e.valid then goto continue end

        local head2d = world_to_screen(e.head)
        if not head2d then goto continue end
        local feet2d = world_to_screen(e.pos)
        if not feet2d then goto continue end

        local h = feet2d.y - head2d.y
        local w = h * 0.5
        local x = head2d.x - w * 0.5

        local r, g_, b = 255, 80, 80
        if e.team == g_local_team and g_local_team ~= 0 then
            r, g_, b = 80, 255, 80
        end

        draw_rect(x, head2d.y, w, h,
                  r, g_, b, 220,
                  1.0, 0.0, 0)
        draw_line(screen_bottom.x, screen_bottom.y,
                  feet2d.x, feet2d.y,
                  255, 255, 255, 120, 1.0)

        local hp = string.format("%d", e.health)
        draw_text(hp, head2d.x - 10, head2d.y - 18,
                  255, 255, 255, 255,
                  get_font18(), 0,
                  0, 0, 0, 0, 0.0)
        ::continue::
    end
end
