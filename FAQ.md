# Frequently Asked Questions <!-- omit in toc -->

- [General](#general)
  - [How can I add additional languages to NormCap?](#how-can-i-add-additional-languages-to-normcap)
  - [What can I do improve the detection accuracy?](#what-can-i-do-improve-the-detection-accuracy)
  - [Is my image analyzed in "the cloud"?](#is-my-image-analyzed-in-the-cloud)
  - [What is the difference between using a pre-build package or a Python package?](#what-is-the-difference-between-using-a-pre-build-package-or-a-python-package)
- [Linux](#linux)
- [Windows](#windows)
- [MacOS](#macos)
  - [How can I start NormCap with a command line argument?](#how-can-i-start-normcap-with-a-command-line-argument)
  - [How can I create a launcher to start NormCap with a certain command line argument?](#how-can-i-create-a-launcher-to-start-normcap-with-a-certain-command-line-argument)
- [Troubleshooting](#troubleshooting)
  - [NormCap is not starting](#normcap-is-not-starting)
  - [\[Linux\] NormCap fails with "Could not load the Qt platform plugin xcb ..."](#linux-normcap-fails-with-could-not-load-the-qt-platform-plugin-xcb-)
  - [\[Linux\] Normcap does not show up in system tray](#linux-normcap-does-not-show-up-in-system-tray)
  - [\[Linux\] Normcap doesn't show a notification after capture](#linux-normcap-doesnt-show-a-notification-after-capture)
- [Development](#development)
  - ["No such file or directory" error when running `briefcase build`](#no-such-file-or-directory-error-when-running-briefcase-build)

## General

### How can I add additional languages to NormCap?

The **prebuild packages** are shipped with the following languages English, German,
Chinese, French, Spanish and Russian. If you miss a language, please
[open an issue](https://github.com/dynobo/normcap/issues).

If you installed NormCap as **Python package**, refer to the online documentation on how
to install additional language for Tesseract on your system.

### What can I do improve the detection accuracy?

The most import thing is to specify the correct language (via settings menu or the
`--language` command line argument). But keep in mind, that selecting multiple languages
at once slows down the recognition a bit.

Tesseract sometimes also struggles with recognizing text with just very view characters,
like a single word. In this case it might help to select a larger portion of text.

If you the results are still quite bad, please submit a screenshot of the text your are
trying to recognize [as an issue](https://github.com/dynobo/normcap/issues).

### Is my image analyzed in "the cloud"?

No. The text recognition is performed offline using the OCR framework
[tesseract](https://github.com/tesseract-ocr/tesseract) and also no other data is send
(e.g. no telemetry data).

### What is the difference between using a pre-build package or a Python package?

Pre-build package:

- Easier to install
- Better system integration
- No admin rights required

Python package:

- Slightly faster startup
- Might need less disk space (depending on your setup)
- Easier to extend with different languages

## Linux

## Windows

## MacOS

### How can I start NormCap with a command line argument?

To run NormCap with an argument _once_, use `open` in the "Terminal" (in
Applications/Utilities) and append NormCap's own options after the `--args` argument.
For example:

```sh
/Applications/NormCap.app/Contents/MacOS/NormCap --help
```

(The command above will list and explain all available arguments.)

### How can I create a launcher to start NormCap with a certain command line argument?

Launch the "Script Editor" and make a new script with the desired command line
arguments, e.g.:

```sh
do shell script "exec /Applications/NormCap.app/Contents/MacOS/NormCap --tray"
```

Save the script as type "Application" in the folder "/Applications"

(When this new Application is started, an additional Icon will show up in the Dock. If
you know a way to avoid this, please open an issue)

## Troubleshooting

### NormCap is not starting

Please try to start again with the `-V` or `--very-verbose` option. This should reveal
more information useful for problem solving.

### \[Linux\] NormCap fails with "Could not load the Qt platform plugin xcb ..."

In case you get the following output...

```
$ normcap --very-verbose
12:06:34 - INFO    - normcap.app            - L:32  - Starting Normcap v0.2.0
12:06:34 - DEBUG   - normcap.utils          - L:199 - [QT] L:0, func: None, file: None
12:06:34 - DEBUG   - normcap.utils          - L:200 - [QT] QtInfoMsg - Could not load the Qt platform plugin "xcb" in "" even though it was found.
12:06:34 - DEBUG   - normcap.utils          - L:199 - [QT] L:0, func: None, file: None
12:06:34 - DEBUG   - normcap.utils          - L:200 - [QT] QtFatalMsg - This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.
```

... the chances are, some system requirements are outdated. You can check this by
`apt list "libxcb-util*"`:

```sh
$ apt list "libxcb-util*"
Listing... Done
libxcb-util-dev/hirsute 0.4.0-1 amd64
libxcb-util-dev/hirsute 0.4.0-1 i386
libxcb-util0-dev/hirsute 0.4.0-1 amd64
libxcb-util0-dev/hirsute 0.4.0-1 i386
libxcb-util1/hirsute,now 0.4.0-1 amd64 [installed,automatic]
libxcb-util1/hirsute 0.4.0-1 i386
```

Is only `libxcb-util0` shown but `libxcb-util1` is missing? Then you can try to create a
symlink for the missing version:

```sh
sudo ln -s /lib/x86_64-linux-gnu/libxcb-util.so.0 /lib/x86_64-linux-gnu/libxcb-util.so.1
```

### \[Linux\] Normcap does not show up in system tray

Is your display environment Gnome Shell? Then you probably need to install a
[Gnome Shell extension](https://extensions.gnome.org/) to support showing applications
in the top bar, e.g.:

- [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/)
- [Ubuntu AppIndicators](https://extensions.gnome.org/extension/1301/ubuntu-appindicators/)
- [Tray Icons](https://extensions.gnome.org/extension/1503/tray-icons/)
- [Tray Icons: Reloaded](https://extensions.gnome.org/extension/2890/tray-icons-reloaded/)

### \[Linux\] Normcap doesn't show a notification after capture

NormCap's notifcations depend on the system tray functionality. Try running normcap with
the `--tray` flag, and if nothing is shown in the system tray, proceed like in the
question above.

## Development

### "No such file or directory" error when running `briefcase build`

To verify, if this is the issue you are facing, run te build docker interactively and
try to run the `linuxdeploy-*.AppImage` file there:

```
docker run -it \
    --volume /home/<USER>/<PROJECT PATH>/normcap/linux:/app:z \
    --volume /home/<USER/.briefcase:/home/brutus/.briefcase:z \
    --env VERSION=0.2.0 briefcase/eu.dynobo.normcap:py3.9 \
    /bin/bash

/home/brutus/.briefcase/tools/linuxdeploy-x86_64.AppImage
```

If that results in a `No such file or directory` error, according to
[this issue](https://github.com/AppImage/AppImageKit/issues/1027#issuecomment-641601097)
and [this one](https://github.com/AppImage/AppImageKit/issues/828) a workaround is to
correct the "magic" bytes of the AppImage. This worked for me:

```
sed '0,/AI\x02/{s|AI\x02|\x00\x00\x00|}' -i linuxdeploy-x86_64.AppImage
```
