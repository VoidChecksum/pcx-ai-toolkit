-- triggerbot.lua — crosshair-trigger logic

-- Engine-specific helper: return the entity under the crosshair.
function get_entity_under_crosshair()
    -- replace with real logic
    return { valid=false, ptr=0, health=0, team=0, pos={x=0,y=0,z=0}, head={x=0,y=0,z=0} }
end

function triggerbot_update()
    if not g_trigger_enabled or not g_initialized or not g_proc or not g_proc:alive() then return end
    if not key_down(g_trigger_key) then return end

    local t = get_entity_under_crosshair()
    if not t.valid then return end
    if t.team == g_local_team and g_local_team ~= 0 then return end
    if t.health <= 0 then return end

    if get_tickcount64() - g_last_fire < g_trigger_delay_ms then return end
    g_last_fire = get_tickcount64()

    mouse_left_click()
end

function triggerbot_render()
    -- no rendering
end
