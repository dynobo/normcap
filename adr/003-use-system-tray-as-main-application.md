# Use system tray as main application

- Status: accepted
- Deciders: @dynobo
- Date: 2022-03-20

## Context and Problem Statement

For QT it is useful to have one widget is as the applications main entry point. This
widget is in charge of orchestrating the main application logic, especially for creating
and managing the multiple windows (multi-monitor use case).

## Decision Drivers

- Support cross platform
- User experience

## Considered Options

- Use one main window as main application which spawns child windows if necessary
  (status quo).
- Use system tray as main application which spawns one (or more) windows.

## Decision Outcome

Chosen option: "Use system tray as main application which spawns one (or more) windows".
_Create_ and _close_ windows for GUI on demand.

It's the only known way to make
[ADR-002](./002-choose-windows-with-screenshots-as-main-gui.md) actually work on macOS
in full-screen.

### Positive Consequences

- Enables showing real full-screens on macOS
- Better code maintenance
    - Get rid of main_window + base_window in favor of a single type of window
    - Better separation between application logic (in tray) and GUI

### Negative Consequences

- The tray icon will show up when starting NormCap. Some users might not like that.

## Pros and Cons of the Options

### Use one main window as main application which spawns child windows if necessary

- Good, because it's status quo, no effort needed.
- Bad, because because it leads to a hard to solve issue on macOS: Whenever windows are
  _hidden_ from full-screen the screen is left back, because the window as the main
  process doesn't free up the display. It's also not possible to unfocused it (move
  focus to a different application or the system). The only way to correctly hide the
  windows is to _close_ them. But as one of this windows is the main application
  process, NormCap will just quit.

### Use system tray as main application which spawns one (or more) windows

- Good, because using the system tray as the main application, solves the black
  full-screen of the status quo on macOS: _create_ windows for selection, then _close_
  (destroy) them immediately. Stay in tray either until the processing finished or
  until the user closes the system tray (in case of "show in tray" is active).
- Bad, because the system tray is necessary, even if "stay in tray" is not active. In
  that case, the system tray just get's closed again immediately after processing the
  OCR.
