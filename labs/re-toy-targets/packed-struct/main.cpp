#include <cstdint>
#include <cstdio>

volatile std::uint32_t g_value = 1337;

int main() {
    std::puts("packed-struct: PlayerHealth");
    return int(g_value == 1337);
}
