# Use jeepney for dbus calls

- Status: accepted
- Deciders: @dynobo
- Date: 2024-01-07

## Context and Problem Statement

## Decision Drivers

- Robustness
- Implementation efforts
- Complexity reduction
- Dependency reduction
- Startup time

## Considered Options

### (A) Stay with [QtDBus](https://doc.qt.io/qtforpython-6/PySide6/QtDBus/index.html)

- Current implementation.

### (B) Switch back to [jeepney](https://pypi.org/project/jeepney/)

- Initially NormCap used to use `jeepney`, but it was removed in favor of QtDBus to get
  rid of that additional dependency and lower the import time.

### (C) Switch to [dbus-next](https://pypi.org/project/dbus-next/)

- The fork [asyncdbus](https://pypi.org/project/asyncdbus/) seems less well spread and
  not significantly better maintained.

### (D) Hybrid QtDbus + jeepney/dbus-next

- Use jeepney/dbus-next only where QtDBus has known issues.

## Decision Outcome

**Chosen option: (B) Switch back to jeepney.**

### Positive Consequences

- Integration with Window Calls extensions becomes possible and increases robustness of
  window positioning on Gnome/Wayland.
- DBus logic can be simplified and easier maintained.
- Fewer workarounds needed.

### Negative Consequences

- It will require initial effort to switch to `jeepney`.
- It will require more effort to switch back to QtDBus, once it becomes stable enough.
- Additional dependency with common risks.
- Additional module adds to import time.

## Pros and Cons of the Options

### (A) Stay with QtDBus

- Good, as no additional dependency required
- Good, as no additional module to add to import time
- Bad, as it seems not widely used and not well maintained (bad documentation, few SO
  topics, few tutorials)
- Bad, as relatively cumbersome to develop with, due to its lower level nature.
- Bad, because it has significant number of flaws/bugs, e.g.:
    - Can't send `u` (int32) datatype, as required for the window ID when using
      `org.gnome.Shell.Extensions.Window`. See
      [#PYSIDE-1904](https://bugreports.qt.io/browse/PYSIDE-1904).
    - Can't reliably
      [decode arguments](https://github.com/dynobo/normcap/blob/d79ef9c1c9ca022066944563c65290ccaadf6a45/normcap/screengrab/dbus_portal.py#L140-L161).

### (B) Switch back to jeepney

- Good, as quite simple to implement
- Good, as it provides a higher level API, stub generator
- Good, as it doesn't have any 3rd party dependencies
- Good, as it provides async api (currently not needed)
- Good, as it provides blocking api
- Bad, as it is an additional dependency for NormCap
- Neutral, as its development isn't very active

### (C) Switch to dbus-next

**Note:** No practical experience with dbus-next, arguments are purely based on docs.

- Good, as quite simple to implement
- Good, as it provides a higher level API, stub generator
- Good, as it doesn't have any 3rd party dependencies
- Good, as it provides async api (currently not needed)
- Bad, as its async event loop can't be easily integrated with Qt's event loop (would
  require the additional dependency [qasync](https://pypi.org/project/qasync/))
- Bad, as it does not provide blocking api
- Bad, as it is an additional dependency for NormCap
- Neutral, as its development isn't very active

### (D) Hybrid QtDbus + jeepney/dbus-next

- Good, as it is easier to switch to preferred QtDbus only, once the issues are solved
- Bad, as implementing with different APIs increases complexity

## References

- e592d132 - refactor(gui): remove qtdbus versions of window positioning
