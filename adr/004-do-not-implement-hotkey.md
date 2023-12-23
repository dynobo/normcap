# Do not implement a hotkey in NormCap

- Status: accepted
- Deciders: @dynobo
- Date: 2023-10-10

## Context and Problem Statement

Currently, the user has to use _the system's built-in capability_ to configure a hotkey,
which provides the ability to trigger NormCap captures via pressing a combination of
keys on the keyboard.

From time to time, users request a feature for configuring a hotkey for NormCap _within_
NormCap's settings. This hotkey should either trigger a new capture if NormCap is
already running in tray, or start NormCap with a capture if it is not already running.
Technically, the difference between those two cases is minor, as in both cases NormCap
needs to react on a key press event _without having focus_. (It only has focus if one of
its windows/dialogs is visible _and_ active.)

A valid argument is, that using the first party system settings for hotkeys can be more
difficult or cumbersome (IMHO this is a very valid concern on Windows).

**Important:** Subject of the discussion is only the process on _how_ this hotkey should
be configured. Once it is set up, the behavior is always the same and currently
implemented as follows:

A hotkey event starts NormCap, _that_ NormCap instance checks, if NormCap is already
running (in system tray):

- If not, it keeps running, performs a capture, and remains in system tray (if
  configured so)
- If yes, it triggers a capture within that _already running_ NormCap instance and exits
  immediately, while letting the earlier instance keep running in system tray.

## Decision Drivers

- User experience
- Cross-platform support
- Maintenance efforts
- Implementation efforts

## Considered Options

### A: Implement _standalone_ hotkey support

Make NormCap itself listen to the global hotkeys and trigger a capture if it was
triggered.

I didn't check, if and how exactly this could be done on all platforms.

### B: Implement _integrated_ hotkey support

NormCap registers itself in the operating systems native hotkey management. How this
could be implemented (after sloppy research):

- macOS: [via defaults write](https://stackoverflow.com/a/7227903)
- Windows: [via native API](https://stackoverflow.com/a/599023)
- Linux: On Gnome via dconf-settings, didn't check KDE and other DEs.

### C: Add link to the OS's native hotkey setting

On Windows, which lacks a central hotkey management, this probably would mean to open
the shortcut's properties?

### D: Do nothing.

Redirect further requests to the documentation
([FAQs entry](https://dynobo.github.io/normcap/#faqs-shortcuts)), which could be
improved, if necessary.

## Decision Outcome

Chosen option: D, do nothing.

The minor UX gain does not justify the significant drawbacks and implementation efforts
of the other options A, B and C.

### Positive Consequences

- Less implementation and maintenance effort.
- Clear separation of responsibilities: The system is/should be responsible for _global_
  hotkey management, not the individual applications.
- User benefit: in midterm, the user might benefit from the knowledge on how to
  configure hotkeys natively, as it works for _all_ applications.

### Negative Consequences

- User struggle or might not be able to achieve configuring a hotkey within the
  operating system. (Especially true for Windows.)

## Pros and Cons of the Options

### A: Implement _standalone_ hotkey support

- Good, enables easy hotkey setup for the user.
- Bad, because it can lead to conflicting hotkey configurations.
- Bad, because of security concerns. Making NormCap able to react on a global hotkey
  basically turns NormCap into a keylogger. Once this ability is implemented (for a
  valid reason), it is much easier to sneak in malicious functionalities into NormCap
  itself. Also, malware might be able to piggyback on NormCap to leverage that
  functionality.
- Bad, because of the security concerns, it might not be possible to implement at all
  cross-platform. E.g., Afaik, this should not be possible on Linux, wayland.

### B: Implement _integrated_ hotkey support

- Good, enables easy hotkey setup for the user.
- Good, as there are no security concerns.
- Bad, because it can lead to conflicting hotkey configurations.
- Bad, because changing system settings from within NormCap is risky: it can have
  unwanted side effects or cause issues if done wrong.
- Bad, because the implementation effort is high, as NormCap has to implement it for all
  platforms. On Linux, often the desktop environment is responsible for the hotkeys,
  so at least supporting KDE and GNOME would be required, others would be desirable as
  well.
- Bad, because it increases maintenance efforts. Especially the Linux DEs are subject of
  changes, which might require adjusting the implementation in NormCap, with all the
  follow-up problems like supporting different DE versions in parallel.

### C: Add link to the OS's native hotkey settings

- Good, as it eases the hotkey setup for the user.
- Good, because it leaves handling hotkey conflicts to the system. (Though Windows
  doesn't, afaik)
- Good, because it nudges people to learn about their systems native hotkey management
- Bad, because the user still has to configure the hotkey by herself, and knowledge on
  how to do that might be missing.
- Bad, because of medium implementation effort, as it needs to be supported on all
  systems and various Linux desktop environments.
- Bad, because it increases maintenance efforts. Especially the Linux DEs are subject of
  changes, which might require adjusting the implementation in NormCap, with all the
  follow-up problems like supporting different DE versions in parallel.

### D: Do nothing

- Good, because it doesn't foster the bad practice of decentralized management of global
  hotkeys. (Debateable!)
- Good, because it nudges people to learn about their systems native hotkey management.
- Good, because no additional effort for implementation or maintenance.
- Bad, because users who are not familiar with there system's hotkey management will
  still struggle with the hotkey configuration or might not be able to do it at all.

## References

- Issues so far: [#538](https://github.com/dynobo/normcap/issues/538),
  [#422](https://github.com/dynobo/normcap/issues/422),
  [#306](https://github.com/dynobo/normcap/issues/306),
  [#103](https://github.com/dynobo/normcap/issues/103)
