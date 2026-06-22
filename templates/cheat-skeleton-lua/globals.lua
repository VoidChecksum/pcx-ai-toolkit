-- globals.lua — shared state and configuration

MAX_ENTITIES = 64

-- Target handles (set in main.lua)
g_proc = nil
g_base = 0
g_size = 0
g_initialized = false

-- Resolved in offsets.lua
g_entity_list = 0
g_local_player = 0
g_view_matrix = 0

-- Team cache
g_local_team = 0

-- Feature toggles
g_esp_enabled     = true
g_aim_enabled     = false
g_trigger_enabled = false
g_radar_enabled   = true

-- Aim settings
g_aim_smooth = 0.15
g_aim_fov    = 30.0
g_aim_key    = 0xA0  -- VK_LSHIFT

-- Trigger settings
g_trigger_key    = 0x12  -- VK_MENU (Alt)
g_trigger_delay_ms = 50
g_last_fire      = 0

-- Entity cache
-- Each entry is a plain table: { valid=false, ptr=0, health=0, team=0, pos={x=0,y=0,z=0}, head={x=0,y=0,z=0} }
g_entities = {}
for i = 1, MAX_ENTITIES do
    g_entities[i] = { valid=false, ptr=0, health=0, team=0, pos={x=0,y=0,z=0}, head={x=0,y=0,z=0} }
end
g_esp_count = 0

-- Active aim target
g_aim_target = { valid=false, ptr=0, health=0, team=0, pos={x=0,y=0,z=0}, head={x=0,y=0,z=0} }

-- Offset constants — replace with real values from your target
OFF_POS    = 0x100  -- UNVERIFIED
OFF_HEALTH = 0x200  -- UNVERIFIED
OFF_TEAM   = 0x300  -- UNVERIFIED
OFF_NAME   = 0x400  -- UNVERIFIED
