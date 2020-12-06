# Default
import os
import sys
from pathlib import Path
import requests

# Extra
import PyInstaller.__main__
import importlib_resources

# Download nsis macro
MACRO_URL = (
    "https://raw.githubusercontent.com/safing/nsis-shortcut-properties/"
    "006b2b62da906c3cad449918a13b83b14e2294ec/shortcut-properties.nsh"
)
response = requests.get(MACRO_URL)
with open("shortcut-properties.nsh", "wb") as f:
    for chunk in response.iter_content(chunk_size=128):
        f.write(chunk)

# WORKAROUND FOR BUG IN PYINSTALLER
(Path(importlib_resources.__file__).parent / "version.txt").touch()

ARGS = [
    "--name=normcap",
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
    f"--add-data=normcap/ressources{os.pathsep}./ressources",
]

if sys.platform.lower().startswith("linux"):
    ARGS.extend(["--add-data=/etc/fonts:fonts", "--runtime-hook=rthook.py"])

if sys.platform.lower().startswith("win"):
    ARGS.extend(
        [
            "--add-data=tessdata;tessdata",
            "--add-data=shortcut-properties.nsh;./",
            "--runtime-hook=rthook.py",
            "--win-private-assemblies",
        ]
    )

ARGS.append(os.path.join("normcap", "__main__.py"))

PyInstaller.__main__.run(ARGS)
