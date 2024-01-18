"""Installs dependencies for running NormCap on various systems.

Used to ease testing NormCap, especially on the different Linux Distros.
The idea is to be able to boot up a VM with a Live CD, run `python deps.py`
and then be able to run any available package of NormCap.

I might even integrate cloning the repo and creating the venv to also be able
to test main, but it's unclear if all this will fit on the Live CD.
"""

import enum
import os
import subprocess
import sys
from pathlib import Path


class System(enum.IntEnum):
    WINDOWS = enum.auto()
    MACOS = enum.auto()
    UBUNTU_XORG = enum.auto()
    UBUNTU_WAYLAND = enum.auto()
    FEDORA_XORG = enum.auto()
    FEDORA_WAYLAND = enum.auto()
    MANJARO_XORG = enum.auto()
    MANJARO_WAYLAND = enum.auto()


def run(cmd: str, check: bool = True) -> str:
    p = subprocess.run(
        cmd,
        shell=True,  # noqa: S602
        check=check,
        capture_output=True,
        encoding="utf-8",
    )
    print(  # noqa: T201
        f"Command {p.args} exited with {p.returncode} code, output: \n{p.stdout}"
    )
    return p.stdout


def display_manager_is_wayland() -> bool:
    xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    has_wayland_display_env = bool(os.environ.get("WAYLAND_DISPLAY", ""))
    return "wayland" in xdg_session_type or has_wayland_display_env


def identify_system() -> System:
    if sys.platform == "win32":
        return System.WINDOWS
    if sys.platform == "darwin":
        return System.MACOS

    is_wayland = display_manager_is_wayland()
    if Path("/etc/lsb-release").exists():
        release = run("cat /etc/lsb-release")
    elif Path("/etc/os-release").exists():
        release = run("cat /etc/os-release")
    else:
        raise RuntimeError("Couldn't read release info.")

    if "Ubuntu" in release:
        return System.UBUNTU_WAYLAND if is_wayland else System.UBUNTU_XORG
    if "ManjaroLinux" in release:
        return System.MANJARO_WAYLAND if is_wayland else System.MANJARO_XORG
    if "Fedora Linux" in release:
        return System.FEDORA_WAYLAND if is_wayland else System.FEDORA_XORG
    raise RuntimeError("Could not identify system.")


def install_deps(system: System) -> None:
    if system == System.UBUNTU_XORG:
        run("sudo add-apt-repository -y universe")
        run("sudo apt install -y libfuse2 libxcb1 libxcb-cursor0")
    if system == System.MANJARO_XORG:
        run("sudo pacman -Sy --noconfirm libxcb xcb-util-cursor libxcrypt-compat")
    if system == System.FEDORA_XORG:
        run("sudo dnf install -y libxcb xcb-util-cursor")


def main() -> None:
    system = identify_system()
    install_deps(system=system)
    run("xdg-open https://github.com/dynobo/normcap/releases")


if __name__ == "__main__":
    main()
