# Choose transparent windows as main GUI

- Status: deprecated
- Deciders: @dynobo
- Date: 2021-10-26

Related issues: #1, #88, #97, #99, #119, #121, #126, #154

## Context and Problem Statement

To offer similar experience to common screenshot tools, we need a main GUI, that covers
all screens and allows to select the region to be transformed into text. It's
surprisingly hard to do this consistently cross platform. Currently the best way to
achieve this seems to be to create a window for each monitor and try to cover its whole
screen area. The windows serve as input and display the frame of the selected region,
but there are different options to make the screen content visible for selection in the
first place.

## Decision Drivers

- Support cross platform
- Support multi-monitor setups
- Support mixed scaling setups (e.g. hidpi monitor + low dpi monitor)
- User experience

## Considered Options

- Use screenshots as background for region-selection windows
- Use transparent backgrounds for region-selection windows

## Decision Outcome

Chosen option: "Use transparent backgrounds for region-selection windows", because it
was the only way I was able to support mixed scaling setups. It's very likely _possible_
to achieve this when using screenshots as backgrounds, too, but it seems much more
complicated.

The decision should be re-evaluated at a later point in time, e.g. when considering
switching to PySide6.

### Positive Consequences

- "Live-view" of the desktop (e.g. videos keep playing), which provides a better UX.
- No need for acquiring the screenshots _before_ region selection.
    - Slightly faster startup
    - Better UX on Gnome 41+, where the screenshot has to be confirmed.

### Negative Consequences

- Requires transparency support by the window manager (doesn't seem to be available for
  all platforms, e.g. some issues with Plasma have been reported)
- It's not possible to show real fullscreen windows on macOS, because the window can't
  be positioned above the application menu bar.

## Pros and Cons of the Options

### Use screenshots as background for region-selection windows

- Good, because it's the only way to provide consistent "real" full-screen windows on
  all platforms (On macOS and Gnome 41+, windows can't fill the whole screen and e.g.
  can't cover menu/application bar, unless they are in "fullscreen" mode. But in that
  mode, the menu/application bar disappears which is bad for UX)
- Bad, because it is really hard to a) get the right dpi settings for each monitor b)
  display the screenshots using the right resolution for each monitor, especially in
  mixed dpi setups.

### Use transparent backgrounds for region-selection windows

- Good, because it's easier to implement
- Good, because the UX on the supported platforms in superior to the alternative
- Bad, because it's not possible to offer real fullscreen experiences on macOS and Gnome
  41+
- Bad, because it seems to have issues on non-transparent window managers (like Plasma
  with the wrong settings)
