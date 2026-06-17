> For the complete documentation index, see [llms.txt](https://enma-1.gitbook.io/enma/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://enma-1.gitbook.io/enma/addons/time.md).

# Time

Registered with `register_addon_time(engine)`.

All timestamps are `int64` microseconds since the Unix epoch (1970-01-01 00:00:00 UTC). Calendar accessors interpret in UTC.

## Current time

```cpp
int64 us = now_us()              // microseconds since epoch
int64 ms = now_ms()              // milliseconds since epoch
int64 ns = now_ns()              // nanoseconds since epoch
int64 s  = unix_seconds()        // seconds since epoch
int64 m  = mono_us()             // monotonic (for deltas; not an epoch)
```

## Calendar accessors

Given a timestamp, extract UTC calendar fields:

```cpp
int64 t = from_ymdhms(2024, 6, 15, 12, 30, 45);
int64 y = year(t)                // 2024
int64 mo = month(t)              // 1..12
int64 d = day(t)                 // 1..31
int64 h = hour(t)                // 0..23
int64 mi = minute(t)             // 0..59
int64 sec = second(t)            // 0..59
int64 dow = day_of_week(t)       // 0=Sun..6=Sat
int64 doy = day_of_year(t)       // 1..366
```

## Leap years / days per month

```cpp
bool  lp = is_leap(2024)                  // true
int64 n  = days_in_month(2024, 2)         // 29 (leap feb)
int64 x  = days_in_month(2024, 13)        // 0 (invalid month)
```

## Construction

```cpp
int64 t1 = from_ymd(2024, 1, 15)                     // midnight UTC
int64 t2 = from_ymdhms(2024, 1, 15, 10, 30, 45)      // full
```

## ISO 8601

Format produces `YYYY-MM-DDTHH:MM:SS.ffffffZ`. Parse accepts the full form, or date-only `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`, optionally with `.ffffff` fractional seconds and trailing `Z`.

```cpp
string iso = iso_format(t)               // "2024-06-15T12:30:45.000000Z"
int64 t2 = iso_parse("2024-06-15")       // midnight UTC of that day
int64 t3 = iso_parse(iso)                // round-trips
```

## Arithmetic

```cpp
int64 later   = add_seconds(t, 60)       // +60s
int64 tomorrow = add_days(t, 1)          // +1 day

int64 du = diff_us(t_later, t_earlier)   // microseconds
int64 dm = diff_ms(t_later, t_earlier)   // milliseconds
int64 ds = diff_s(t_later, t_earlier)    // seconds
```

## Sleep

```cpp
sleep_ms(100)                             // suspend 100ms
```


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://enma-1.gitbook.io/enma/addons/time.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
