> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/render-api.md).

# Render API

### Constants

```lua
RR_TOP_LEFT
RR_TOP_RIGHT
RR_BOTTOM_LEFT
RR_BOTTOM_RIGHT
```

Rectangle corner rounding flags (bitmask), used with `rounding_flags` in rect functions.

```lua
TE_NONE
TE_OUTLINE
TE_SHADOW
TE_GLOW
```

Text effects used by `draw_text`.

***

### Viewport

```lua
w, h = get_view()
scale = get_view_scale()
fps = get_fps()
```

* `get_view()` — returns the current viewport width and height in pixels.
* `get_view_scale()` — returns a reference scale factor (useful for DPI-aware sizes).
* `get_fps()`

***

### Shapes

#### Rectangle (outline)

```lua
draw_rect(x, y, w, h,
          r, g, b, a,
          thickness, rounding, rounding_flags)
```

Draws a rounded rectangle outline.

***

#### Rectangle (filled)

```lua
draw_rect_filled(x, y, w, h,
                 r, g, b, a,
                 rounding, rounding_flags)
```

Draws a filled rounded rectangle.

***

#### Line

```lua
draw_line(x1, y1, x2, y2,
          r, g, b, a,
          thickness)
```

Draws a line from `(x1, y1)` to `(x2, y2)`.

***

#### Arc

```lua
draw_arc(cx, cy, rx, ry,
         start_angle_deg, sweep_angle_deg,
         r, g, b, a,
         thickness, filled)
```

Draws an arc or pie-slice centered at `(cx, cy)`.

***

#### Circle

```lua
draw_circle(cx, cy, radius,
            r, g, b, a,
            thickness, filled)
```

Draws a circle centered at `(cx, cy)`.

* If `filled == true`, draws a filled circle.
* Otherwise draws an outlined circle.

***

#### Triangle

```lua
draw_triangle(ax, ay, bx, by, cx, cy,
              r, g, b, a,
              thickness, filled)
```

Draws a triangle using the three points `(ax, ay)`, `(bx, by)`, `(cx, cy)`.

***

#### Polygon

```lua
draw_polygon(xy_pairs, count_pairs,
             r, g, b, a,
             thickness, filled)
```

* `xy_pairs` — Lua table of floats: `{ x1, y1, x2, y2, x3, y3, ... }`.
* `count_pairs` — optional; if `nil` or `0`, uses the whole table.

Draws a polyline or filled polygon.

***

#### Four-Corner Gradient

```lua
draw_four_corner_gradient(x, y, w, h,
                          tlr, tlg, tlb, tla,
                          trr, trg, trb, tra,
                          blr, blg, blb, bla,
                          brr, brg, brb, bra,
                          rounding)
```

Draws a rectangle with independent colors per corner:

* top-left: `(tlr, tlg, tlb, tla)`
* top-right: `(trr, trg, trb, tra)`
* bottom-left: `(blr, blg, blb, bla)`
* bottom-right: `(brr, brg, brb, bra)`

***

### Bitmaps

#### Create bitmap

```lua
bmp = create_bitmap(data)
```

* `data` — Lua table of `uint8` values (byte buffer).
* Returns a handle `bmp` that can be passed to `draw_bitmap`.
* Returns `0` on failure.

***

#### Draw bitmap

```lua
draw_bitmap(bmp, x, y, w, h,
            r, g, b, a,
            rounded)
```

Draws a bitmap tinted with color `(r, g, b, a)`.

* `bmp` — handle returned by `create_bitmap`.
* `rounded` — if `true`, draws with rounded corners.

***

### Fonts & Text

#### Built-in fonts

```lua
font = get_font18()
font = get_font20()
font = get_font24()
font = get_font28()
```

Returns a handle to a default font at a given size.

***

#### Create font from file

```lua
font = create_font(path, size, anti_aliased, load_color, optional:glyph_ranges)
```

* `path` — filesystem path or font name.
* `size` — font size in pixels.
* `anti_aliased` — `true` for smooth text, `false` for pixel-style rendering (boolean).
* `load_color` — `true` to enable color glyphs (emoji / color fonts), `false` for standard monochrome glyphs (boolean).
* `glyph_ranges`  — array of custom glyph ranges
* Returns a font handle or `0` on failure.

The function searches for fonts inside the API directory (e.g. `verdana_custom.ttf`, `fonts/verdana_custom.ttf`) and may fall back to system font locations.\
If a font name matches a system font, that one may be loaded instead— use unique names to prevent conflicts.

***

#### Create font from memory

```lua
font = create_font_mem(label, size, buf , anti_aliased, load_color, optional:glyph_ranges)
```

* `label` — name/tag for the font (string).
* `size` — font size in pixels.
* `buf` — Lua table of `uint8` values (font binary data).
* `anti_aliased` — `true` for smooth text, `false` for pixel-style rendering (boolean).
* `load_color` — `true` to enable color glyphs (emoji / color fonts), `false` for standard monochrome glyphs (boolean).
* `glyph_ranges`  — array of custom glyph ranges
* Returns a font handle or `0` on failure.

***

#### Using custom glyph ranges

```lua
local ranges = {
    0x0020, 0x00FF,   -- Basic Latin + Latin-1 Supplement
    0x0400, 0x04FF,   -- Cyrillic
    0
}
local font2 = create_font("Arial", 16.0, true, false, ranges)
```

***

#### Draw text

```lua
draw_text(text, x, y,
          r, g, b, a,
          font, effect,
          er, eg, eb, ea,
          effect_amount)
```

* `text` — string to draw.
* `(r, g, b, a)` — text color.
* `font` — font handle.
* `effect` — one of `TE_NONE`, `TE_OUTLINE`, `TE_SHADOW`, `TE_GLOW`.
* `(er, eg, eb, ea)` — effect color (e.g. shadow/outline color).
* `effect_amount` — intensity scalar.

***

#### Text metrics

```lua
w, h = get_text_size(font, text,
                     maxw, maxh)

advance = get_char_advance(font, wchar32)
```

* `get_text_size` — returns width/height of the rendered `text`.
* `get_char_advance` — returns advance width for a single character (`wchar32`).

***

### Clipping

```lua
clip_push(x, y, w, h)
clip_pop()
```

* `clip_push` — pushes a rectangular clip region.
* `clip_pop` — restores the previous clip region.

All drawing while a clip is active is restricted to the specified rectangle.

***

### Example

```lua
local font = 0
local t = 0

function main()
    log("Lua render example loaded.")

    -- Use built-in default font
    font = get_font20()

    return 1 -- keep script running
end

function on_frame()
    -- Get viewport
    local vw, vh = get_view()
    local scale  = get_view_scale()

    t = t + 1

    -- Panel size
    local w  = 260 * scale
    local h  = 120 * scale
    local cx = vw * 0.5
    local cy = vh * 0.5
    local x  = cx - w * 0.5
    local y  = cy - h * 0.5

    -- Background panel
    draw_rect_filled(
        x, y, w, h,
        30, 30, 40, 230,      -- r,g,b,a
        8.0 * scale,          -- rounding
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
    )

    -- Outline
    draw_rect(
        x, y, w, h,
        80, 140, 255, 255,    -- r,g,b,a
        2.0 * scale,          -- thickness
        8.0 * scale,          -- rounding
        RR_TOP_LEFT | RR_TOP_RIGHT | RR_BOTTOM_LEFT | RR_BOTTOM_RIGHT
    )

    -- Animated accent bar
    local bar_h = 4 * scale
    draw_rect_filled(
        x, y - bar_h - 2 * scale, w, bar_h,
        120 + (t % 60), 80, 220, 255,
        2.0 * scale,
        RR_TOP_LEFT | RR_TOP_RIGHT
    )

    -- Text
    local title = "Lua Render API"
    local w_text, h_text = get_text_size(font, title, 1000, 1000)

    local tx = cx - w_text * 0.5
    local ty = cy - h_text * 0.5 - 10 * scale

    draw_text(
        title,
        tx, ty,
        255, 255, 255, 255,  -- text color
        font,
        TE_SHADOW,           -- effect
        0, 0, 0, 180,        -- effect color (shadow)
        1.0,                 -- effect amount
    )

    -- Subtitle
    local subtitle = "drawing from Lua 5.4.6"
    local sw, sh = get_text_size(font, subtitle, 1000, 1000)
    local sx = cx - sw * 0.5
    local sy = ty + h_text + 8 * scale

    draw_text(
        subtitle,
        sx, sy,
        180, 200, 255, 255,
        font,
        TE_NONE,
        0, 0, 0, 0,
        0.0
    )
end

function on_unload()
    log("Lua render example unloading.")
end

```

This draws a centered rounded panel and a title text using the Lua Render API.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/render-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
