> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/lua-script/sound-api.md).

# Sound API

The Sound API lets Lua scripts load and play audio files with real-time volume and stereo panning control.

Sound files are loaded from relative paths resolved against your script directory (same as the File System API).

**Supported formats:** WAV (PCM 8/16-bit), MP3, AAC, WMA, FLAC — anything Windows Media Foundation can decode.

All audio is resampled to 44100 Hz stereo at load time. Up to 64 sounds can play simultaneously.

***

### Concepts

There are two handle types, both represented as integers:

* **Sound handle** — a loaded audio resource returned by `load_sound`. Can be played multiple times simultaneously. Must be freed with `free_sound` when no longer needed.
* **Instance handle** — a single playing occurrence returned by `play_sound`. Used to stop, query, or adjust an active playback.

Both return `0` on failure. All functions are safe to call with `0` handles (they become no-ops).

***

### Loading & Freeing

**`load_sound(path) -> handle`**

Loads a sound file from a relative path.

* `path` (string) — Relative path to the audio file (e.g. `"sounds/hit.wav"`, `"alert.mp3"`).

Returns a sound handle (integer), or `0` if the file doesn't exist or decoding fails.

***

**`free_sound(handle)`**

Frees a previously loaded sound resource. Any active instances using this sound are stopped automatically.

***

### Playback

**`play_sound(sound [, volume [, pan [, loop]]]) -> instance`**

Plays a loaded sound and returns an instance handle.

* `sound` (integer) — Sound handle from `load_sound`.
* `volume` (number) — `0.0` (silent) to `1.0` (full). Default `1.0`. Clamped.
* `pan` (number) — `-1.0` (full left) to `+1.0` (full right). Default `0.0` (center). Clamped.
* `loop` (boolean) — If `true`, the sound repeats until explicitly stopped. Default `false`.

Returns an instance handle (integer), or `0` if the sound handle is invalid or all 64 instance slots are in use.

***

**`stop_sound(instance)`**

Stops a playing instance immediately.

***

**`stop_all_sounds()`**

Stops every currently playing sound instance.

***

**`is_sound_playing(instance) -> bool`**

Returns `true` if the instance is still actively playing. Returns `false` if it finished, was stopped, or the handle is invalid.

***

### Live Adjustment

These functions modify a playing instance in real time. Changes take effect on the next mixer tick (\~20ms).

**`set_sound_volume(instance, volume)`**

Changes volume of a playing instance. `0.0` to `1.0`, clamped.

***

**`set_sound_pan(instance, pan)`**

Changes stereo panning of a playing instance. `-1.0` (left) to `+1.0` (right), clamped.

***

### Examples

#### Play a one-shot sound effect

```lua
local snd = 0

function main()
    snd = load_sound("pop.mp3")
    if snd == 0 then
        log("Failed to load sound")
        return 0
    end

    play_sound(snd, 0.8, 0.0)
    return 1
end

function on_unload()
    if snd ~= 0 then free_sound(snd) end
end
```

***

#### Looping background music

```lua
local music = 0
local music_inst = 0

function main()
    music = load_sound("ambient.ogg")
    if music ~= 0 then
        music_inst = play_sound(music, 0.5, 0.0, true)
    end
    return 1
end

function on_unload()
    if music_inst ~= 0 then stop_sound(music_inst) end
    if music ~= 0 then free_sound(music) end
end
```

***

#### Directional sound with panning

```lua
local function play_hit(snd, target_x, player_x, max_range)
    local pan = (target_x - player_x) / max_range
    if pan < -1.0 then pan = -1.0 end
    if pan >  1.0 then pan =  1.0 end

    play_sound(snd, 1.0, pan)
end
```

***

#### Fade out over time

```lua
local snd = 0
local inst = 0
local vol = 1.0

function main()
    snd = load_sound("alert.wav")
    if snd == 0 then return 0 end

    inst = play_sound(snd, 1.0, 0.0)
    return 1
end

function on_frame()
    if inst == 0 then return end

    vol = vol - 0.02
    if vol <= 0.0 then
        stop_sound(inst)
        inst = 0
        return
    end

    set_sound_volume(inst, vol)
end

function on_unload()
    if inst ~= 0 then stop_sound(inst) end
    if snd ~= 0 then free_sound(snd) end
end
```

***

#### Multiple simultaneous sounds

```lua
function main()
    local snd = load_sound("hit.wav")
    if snd == 0 then return 0 end

    play_sound(snd, 1.0,  0.0)
    play_sound(snd, 0.7, -0.5)
    play_sound(snd, 0.5,  0.8)

    return 1
end
```

***

### Notes

* Sound data is fully decoded to PCM at load time. Loading is the expensive operation — `play_sound` is cheap.
* Instance handles point into a fixed pool of 64 slots. If all slots are in use, `play_sound` returns `0`.
* Calling `free_sound` automatically stops all instances that reference that sound.
* Sounds are automatically freed when your script is unloaded (leaked handles are cleaned up). You should still free sounds explicitly when possible.
* The `path` parameter follows the same validation rules as the File System API: relative paths only, no `..` segments, no `:` characters.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://docs.perception.cx/perception/lua-script/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
