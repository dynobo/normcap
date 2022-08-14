# Choose windows with screenshots as main GUI

- Status: accepted
- Deciders: @dynobo
- Date: 2022-03-20

**Revision of ADR [#001](001-choose-transparent-windows-as-main-gui.md)**

## Context and Problem Statement

To offer similar experience to common screenshot tools, we need a main GUI, that covers
all screens and allows to select the region to be transformed into text. It's
surprisingly hard to do this consistently cross platform. Currently the best way to
achieve this seems to be to create a window for each monitor and try to cover its whole
screen area. The windows serve as input and display the frame of the selected region,
but there are different options to make the screen content visible for selection in the
first place.

## Decision Drivers

- **Support Python 3.10+**
- Support cross platform
- Support multi-monitor setups
- Support mixed scaling setups (e.g. hidpi monitor + low dpi monitor)
- User experience

## Considered Options

- Use screenshots as background for region-selection windows
- Use transparent backgrounds for region-selection windows

## Decision Outcome

Chosen option: "Use screenshots as background for region-selection windows", because the
switch to PySide6 is inevitable (due to lacking support of PySide2 for Python 3.10 and
deprecation). With PySide6 the workarounds for creating a "normal" window that covers
the whole screen don't work anymore, e.g. on Wayland. "Fullscreen" windows on the other
hand *hide* the top bar on Wayland and macOS, which is bad UX. Therefore setting
screenshots as backgrounds seemed to be the currently best solution, even if it is more
complicated to implement, especially in mixed scaling setups.

### Positive Consequences

- Better experience on macOS (finally covering the whole screen).
- Technical benefits (better supported QT version; Python 3.10+).
- Doesn't require a window manager with transparency support.

### Negative Consequences

- Worse UX in general, as no "Live" view of the Desktop anymore
- Slightly slower startup (screenshots have to be taken and scaled)
- Worse UX on Gnome 41+, where the screenshot has to be confirmed on startup.

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
