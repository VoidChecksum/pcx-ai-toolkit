> For the complete documentation index, see [llms.txt](https://docs.perception.cx/perception/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://docs.perception.cx/perception/angel-script/sound-api.md).

# Sound API

The Sound API lets AngelScript scripts load and play audio files with real-time volume and stereo panning control.

Sound files are loaded from relative paths resolved against your script directory (same as the File System API).

**Supported formats:** WAV (PCM 8/16-bit), MP3, AAC, WMA, FLAC — anything Windows Media Foundation can decode.

All audio is resampled to 44100 Hz stereo at load time. Up to 64 sounds can play simultaneously.

***

### Concepts

There are two handle types, both represented as `uint64`:

* **Sound handle** — a loaded audio resource returned by `load_sound`. Can be played multiple times simultaneously. Must be freed with `free_sound` when no longer needed.
* **Instance handle** — a single playing occurrence returned by `play_sound`. Used to stop, query, or adjust an active playback.

Both return `0` on failure. All functions are safe to call with `0` handles (they become no-ops).

***

### Loading & Freeing

**`uint64 load_sound(const string &in path)`**

Loads a sound file from a relative path.

* `path` — Relative path to the audio file (e.g. `"sounds/hit.wav"`, `"alert.mp3"`).

Returns a sound handle, or `0` if the file doesn't exist or decoding fails.

***

**`void free_sound(uint64 handle)`**

Frees a previously loaded sound resource. Any active instances using this sound are stopped automatically.

***

### Playback

**`uint64 play_sound(uint64 sound, float volume = 1.0, float pan = 0.0, bool loop = false)`**

Plays a loaded sound and returns an instance handle.

* `sound` — Sound handle from `load_sound`.
* `volume` — `0.0` (silent) to `1.0` (full). Clamped.
* `pan` — `-1.0` (full left) to `+1.0` (full right). `0.0` is center. Clamped.
* `loop` — If `true`, the sound repeats until explicitly stopped.

Returns an instance handle, or `0` if the sound handle is invalid or all 64 instance slots are in use.

***

**`void stop_sound(uint64 instance)`**

Stops a playing instance immediately.

***

**`void stop_all_sounds()`**

Stops every currently playing sound instance.

***

**`bool is_sound_playing(uint64 instance)`**

Returns `true` if the instance is still actively playing. Returns `false` if it finished, was stopped, or the handle is invalid.

***

### Live Adjustment

These functions modify a playing instance in real time. Changes take effect on the next mixer tick (\~20ms).

**`void set_sound_volume(uint64 instance, float volume)`**

Changes volume of a playing instance. `0.0` to `1.0`, clamped.

***

**`void set_sound_pan(uint64 instance, float pan)`**

Changes stereo panning of a playing instance. `-1.0` (left) to `+1.0` (right), clamped.

***

### Examples

#### Play a one-shot sound effect

```cpp
uint64 snd = 0;

int main()
{
    snd = load_sound("pop.mp3");
    if (snd == 0)
    {
        log("Failed to load sound");
        return 0;
    }

    play_sound(snd, 0.8f, 0.0f);
    return 1;
}

void on_unload()
{
    if (snd != 0)
        free_sound(snd);
}
```

***

#### Looping background music

```cpp
uint64 music = 0;
uint64 music_inst = 0;

int main()
{
    music = load_sound("ambient.ogg");
    if (music != 0)
        music_inst = play_sound(music, 0.5f, 0.0f, true);

    return 1;
}

void on_unload()
{
    if (music_inst != 0)
        stop_sound(music_inst);
    if (music != 0)
        free_sound(music);
}
```

***

#### Directional sound with panning

```cpp
void play_hit(uint64 snd, float target_x, float player_x, float max_range)
{
    float pan = (target_x - player_x) / max_range;
    if (pan < -1.0f) pan = -1.0f;
    if (pan >  1.0f) pan =  1.0f;

    play_sound(snd, 1.0f, pan);
}
```

***

#### Adjusting volume over time

```cpp
uint64 snd = 0;
uint64 inst = 0;
int cb = 0;
float vol = 1.0f;

void fade_out(int id, int data)
{
    if (inst == 0) return;

    vol -= 0.02f;
    if (vol <= 0.0f)
    {
        stop_sound(inst);
        inst = 0;
        return;
    }

    set_sound_volume(inst, vol);
}

int main()
{
    snd = load_sound("alert.wav");
    if (snd == 0) return 0;

    inst = play_sound(snd, 1.0f, 0.0f);
    cb = register_callback(@fade_out, 50, 0);
    return 1;
}

void on_unload()
{
    if (cb != 0) unregister_callback(cb);
    if (inst != 0) stop_sound(inst);
    if (snd != 0) free_sound(snd);
}
```

***

#### Multiple simultaneous sounds

```cpp
int main()
{
    uint64 snd = load_sound("hit.wav");
    if (snd == 0) return 0;

    play_sound(snd, 1.0f,  0.0f);
    play_sound(snd, 0.7f, -0.5f);
    play_sound(snd, 0.5f,  0.8f);

    return 1;
}
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
GET https://docs.perception.cx/perception/angel-script/sound-api.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
