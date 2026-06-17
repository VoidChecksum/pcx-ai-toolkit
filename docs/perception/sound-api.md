> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/enma/sound-api.md).

# Sound API

All sound natives are auto-registered into every loaded script.

Two handle types:

* `sound_t` — a loaded resource. Multiple instances can play from one resource concurrently.
* `sound_inst_t` — a live playback instance. Returned by `sound.play(...)`.

Both are `int64`-backed handles with auto-cleanup destructors. Resources are tracked per-script; an unload sweep frees anything the user forgot to drop.

## Load / unload

```cpp
sound_t load_sound(string relative_path);
```

Loads `<my_games>/<relative_path>`. Path is validated:

* No `..` segments.
* No `:` (drive letters), `\n`, `\r`.
* Cannot start with `/` or `\` (must be relative).

Returns a null handle on validation failure or read failure. The destructor frees the resource.

## Playback

```cpp
sound_inst_t sound.play(float64 volume, float64 pan, bool loop);
```

* `volume`: 0.0 .. 1.0 (clamped)
* `pan`: -1.0 (full left) .. 1.0 (full right) (clamped)
* `loop`: repeat forever until stopped

## Instance control

```cpp
bool sound_inst.is_playing();
void sound_inst.stop();
void sound_inst.set_volume(float64 v);    // 0..1
void sound_inst.set_pan(float64 p);       // -1..1
```

## Globals

```cpp
void stop_all_sounds();    // halts every instance globally
```

## Example

```cpp
int64 main() {
    sound_t snd = load_sound("sounds/notification.wav");
    if (cast<int64>(snd) == 0) return 0;

    sound_inst_t inst = snd.play(0.5, 0.0, false);
    while (inst.is_playing()) sleep_ms(50);

    return 1;
    // snd / inst drop here; resource + instance freed
}
```

## Lifetime

`sound_t` and `sound_inst_t` both release at scope exit. If the script forgets, the host sweeps remaining handles at unload. No permanent leak.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/enma/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
