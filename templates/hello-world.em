// hello-world.em — minimal Enma script for Perception.cx
// Demonstrates: lifecycle (main + return value), a render routine, basic drawing.
// See docs/perception/lifecycle-and-routines.md and docs/perception/render-api.md

import "vec";
import "color";

// Render routine — runs every frame after main() returns.
// The single int64 parameter is the user-data passed to register_routine.
void on_render(int64 data) {
    color white  = color(255, 255, 255, 255);
    color shadow = color(0, 0, 0, 180);
    draw_text("Hello from Enma", vec2(20.0, 20.0), white, get_font20(), 1, shadow, 1.0);
}

int64 main() {
    // register_routine takes a function handle (cast<int64>) + user data.
    register_routine(cast<int64>(on_render), 0);

    // return > 0 keeps the script loaded; <= 0 unloads immediately.
    return 1;
}
