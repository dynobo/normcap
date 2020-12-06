import sys


def _post_install_win():
    # Creates a Desktop shortcut to the installed software
    from pathlib import Path
    import sysconfig
    from importlib_resources import files  # type: ignore
    from win32com.client import Dispatch  # type: ignore

    # Package name
    NAME = "Normcap"
    WORKDIR_PATH = Path(sysconfig.get_path("scripts"))
    TARGET_PATH = WORKDIR_PATH / "normcap.exe"

    # Path to location of link file
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(NAME)
    shortcut.Targetpath = TARGET_PATH
    shortcut.WorkingDirectory = WORKDIR_PATH
    shortcut.Description = "OCR powered screen-capture tool"
    shortcut.IconLocation = (
        files("normcap").joinpath("ressources").joinpath("normcap.png")
    )
    shortcut.save()


if sys.argv[1] == "install" and sys.platform == "win32":
    _post_install_win()
