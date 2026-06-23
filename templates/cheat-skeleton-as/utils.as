// utils.as — W2S, distance, team helpers
namespace Cheat {

const double PI = 3.14159265358979323846;
const double RAD2DEG = 180.0 / PI;
const double DEG2RAD = PI / 180.0;

// Read a 3-float vector from a memory address.
vector3 read_vec3(uint64 addr) {
    if (addr == 0) return vector3(0,0,0);
    double x = g_proc.rf32(addr + 0);
    double y = g_proc.rf32(addr + 4);
    double z = g_proc.rf32(addr + 8);
    return vector3(x, y, z);
}

// Pointer-chain reader.
uint64 read_chain(uint64 base, const array<int> &in offsets) {
    uint64 addr = base;
    for (uint i = 0; i < offsets.length(); i++) {
        if (addr == 0) return 0;
        addr = g_proc.ru64(addr);
        if (addr == 0) return 0;
        addr += uint64(offsets[i]);
    }
    return addr;
}

double distance3d(const vector3&in a, const vector3&in b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    double dz = a.z - b.z;
    return sqrt(dx*dx + dy*dy + dz*dz);
}

bool world_to_screen(const vector3&in world, vector2&out screen) {
    if (g_view_matrix == 0) return false;

    double m[16];
    for (int i = 0; i < 16; i++) {
        m[i] = g_proc.rf32(g_view_matrix + uint64(i * 4));
    }

    double w = m[3]*world.x + m[7]*world.y + m[11]*world.z + m[15];
    if (w < 0.001) return false;

    double inv_w = 1.0 / w;
    double nx = (m[0]*world.x + m[4]*world.y + m[8]*world.z + m[12]) * inv_w;
    double ny = (m[1]*world.x + m[5]*world.y + m[9]*world.z + m[13]) * inv_w;

    float vw;
    float vh;
    get_view(vw, vh);
    screen.x = (vw * 0.5) + (nx * vw * 0.5);
    screen.y = (vh * 0.5) - (ny * vh * 0.5);
    return true;
}

vector2 calc_angle(const vector3&in src, const vector3&in dst) {
    vector3 d = dst - src;
    double dist_xy = sqrt(d.x*d.x + d.y*d.y);
    double pitch = atan2(-d.z, dist_xy) * RAD2DEG;
    double yaw   = atan2(d.y, d.x) * RAD2DEG;
    return vector2(pitch, yaw);
}

double normalize_delta(double delta) {
    return fmod(delta + 540.0, 360.0) - 180.0;
}

vector3 angles_to_forward(double pitch_deg, double yaw_deg) {
    double p = pitch_deg * DEG2RAD;
    double y = yaw_deg   * DEG2RAD;
    double cp = cos(p);
    return vector3(cp * cos(y), cp * sin(y), -sin(p));
}

bool in_fov(const vector3&in src, const vector2&in view_angles, const vector3&in target, double fov_deg) {
    vector3 dir = target - src;
    double len = sqrt(dir.x*dir.x + dir.y*dir.y + dir.z*dir.z);
    if (len == 0.0) return false;
    dir = vector3(dir.x / len, dir.y / len, dir.z / len);

    vector3 fwd = angles_to_forward(view_angles.x, view_angles.y);
    double dot = fwd.x*dir.x + fwd.y*dir.y + fwd.z*dir.z;
    return dot >= cos(fov_deg * DEG2RAD);
}

}
