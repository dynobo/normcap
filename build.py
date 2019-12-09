import PyInstaller.__main__
import os

ARGS = [
    "--name=NormCap",
    "--clean",
    "--noconfirm",
    # "--onefile",
    "--onedir",
    "--windowed",
    # "--debug=all",
    "--log-level=DEBUG",
    f"--icon={os.path.join('ressource', 'normcap.ico')}",
    f"--paths={os.path.join('.venv', 'lib', 'python3.7', 'site-packages')}",
    "--hidden-import=PIL._imagingtk",
    "--hidden-import=PIL._tkinter_finder",
]

if False:
    ARGS.extend(["--add-data=/etc/fonts:fonts", "--runtime-hook=rthook.py"])

ARGS.append(os.path.join("normcap", "__main__.py"))

PyInstaller.__main__.run(ARGS)
