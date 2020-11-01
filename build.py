# Default
import os
import sys
from pathlib import Path

# Extra
import PyInstaller.__main__
import importlib_resources

# Own
import normcap

# WORKAROUND FOR BUG IN PYINSTALLER
(Path(importlib_resources.__file__).parent / "version.txt").touch()

ARGS = [
    f"--name=normcap-v{normcap.__version__}",
    "--clean",
    "--noconfirm",
    # "--onefile",
    "--onedir",
    "--windowed",
    # "--debug=all",
    # "--log-level=DEBUG",
    f"--icon={os.path.join('normcap','ressources', 'normcap.ico')}",
    f"--paths={os.path.join('.venv', 'lib', 'python3.8', 'site-packages')}",
    "--hidden-import=PIL",
    "--hidden-import=PIL._imagingtk",
    "--hidden-import=PIL._tkinter_finder",
    "--hidden-import=importlib_resources.trees",
    "--runtime-hook=rthook.py",
    f"--add-data=normcap/ressources{os.pathsep}normcap/ressources",
]

if sys.platform.lower().startswith("linux"):
    ARGS.extend(["--add-data=/etc/fonts:fonts", "--runtime-hook=rthook.py"])

if sys.platform.lower().startswith("win"):
    ARGS.extend(
        [
            "--add-data=tessdata;tessdata",
            "--runtime-hook=rthook.py",
            "--win-private-assemblies",
        ]
    )

ARGS.append(os.path.join("normcap", "__main__.py"))

PyInstaller.__main__.run(ARGS)
