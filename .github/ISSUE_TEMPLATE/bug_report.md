---
name: Bug report
about: Create a report to help us improve
title: ''
labels: 'bug'
assignees: ''

---

**Describe the bug:** 

A description of what the problem is. Include screenshots, if
useful.

**System information:**

- Operating System: [e.g. Windows 11, macOS Ventura, Ubuntu 23.03, Fedora 37, Arch]
- NormCap installation method: [e.g. Python package, MSI, DMG, AppImage, AUR, Microsoft
  Store]
- (Linux only) Display Server : [e.g. XOrg, Wayland]

**Debug output:** 

Please start NormCap with `-v debug` option from the command line,
reproduce the bug and post the output printed in the terminal:

```
paste debug output here
```

<!--
Hint: The command to start normcap with the debug option depends on how you have installed it:

- Python package:
  normcap -v debug

- MSI installer:
  %LOCALAPPDATA%\Programs\dynobo\NormCap\NormCap.exe -- -v debug

- DMG installer:
  /Applications/NormCap.app/Contents/MacOS/NormCap -v debug

- AppImage:
  ./NormCap-{version}-x86_64.AppImage -v debug

- Flatpak:
  flatpak run --command=normcap com.github.dynobo.normcap -v debug

- AUR:
  normcap -v debug
-->
