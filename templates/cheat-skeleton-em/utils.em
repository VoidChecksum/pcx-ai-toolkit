// utils.em — W2S, distance, team helpers
#pragma once

import "globals";
import "math";
import "vec";

const float64 PI = 3.14159265358979323846;
const float64 RAD2DEG = 180.0 / PI;
const float64 DEG2RAD = PI / 180.0;

// Read a 3-float vector from a memory address.
vec3 read_vec3(uint64 addr) {
    if (addr == 0) return vec3(0,0,0);
    float64 x = g_proc.rf32(addr + 0);
    float64 y = g_proc.rf32(addr + 4);
    float64 z = g_proc.rf32(addr + 8);
    return vec3(x, y, z);
}

// Pointer-chain reader.
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

float64 distance3d(vec3 a, vec3 b) {
    float64 dx = a.x - b.x;
    float64 dy = a.y - b.y;
    float64 dz = a.z - b.z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

bool world_to_screen(vec3 world, out vec2 screen) {
    if (g_view_matrix == 0) return false;

    float64 m[16];
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
    screen.x = (vw * 0.5) + (nx * vw * 0.5);
    screen.y = (vh * 0.5) - (ny * vh * 0.5);
    return true;
}

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

vec3 angles_to_forward(float64 pitch_deg, float64 yaw_deg) {
    float64 p = pitch_deg * DEG2RAD;
    float64 y = yaw_deg   * DEG2RAD;
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
    return dot >= cos(fov_deg * DEG2RAD);
}
