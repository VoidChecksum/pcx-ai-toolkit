import "vec";
import "color";

void draw(int64 data) {
    draw_text("scenario", vec2(16.0, 16.0), color(255,255,255,255), get_font20(), 0, color(0,0,0,0), 0.0);
}

int64 main() {
    register_routine(cast<int64>(draw), 0);
    return 1;
}
