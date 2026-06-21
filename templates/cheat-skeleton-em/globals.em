// globals.em — shared state and configuration
#pragma once

import "proc";
import "vec";
import "math";
import "color";

const int32 MAX_ENTITIES = 64;

// Target handles (set in main.em)
proc_t g_proc;
uint64 g_base = 0;
uint64 g_size = 0;
bool g_initialized = false;

// Resolved in offsets.em
uint64 g_entity_list = 0;
uint64 g_local_player = 0;
uint64 g_view_matrix = 0;

// Team cache
int32 g_local_team = 0;

// Feature toggles
bool g_esp_enabled     = true;
bool g_aim_enabled     = false;
bool g_trigger_enabled = false;
bool g_radar_enabled   = true;

// Aim settings
float64 g_aim_smooth = 0.15;
float64 g_aim_fov    = 30.0;
int32   g_aim_key    = VK_LSHIFT;   // hold key

// Trigger settings
int32   g_trigger_key   = VK_LMENU; // Alt
int32   g_trigger_delay_ms = 50;
int64   g_last_fire = 0;

// Entity cache
struct EntityInfo {
    bool    valid   = false;
    uint64  ptr     = 0;
    int32   health  = 0;
    int32   team    = 0;
    vec3    pos     = vec3(0,0,0);
    vec3    head    = vec3(0,0,0);
};

EntityInfo g_entities[MAX_ENTITIES];
int32 g_esp_count = 0;

// Active aim target
EntityInfo g_aim_target;

// Offset constants — replace with real values from your target
const uint64 OFF_POS    = 0x100; // UNVERIFIED
const uint64 OFF_HEALTH = 0x200; // UNVERIFIED
const uint64 OFF_TEAM   = 0x300; // UNVERIFIED
const uint64 OFF_NAME   = 0x400; // UNVERIFIED
