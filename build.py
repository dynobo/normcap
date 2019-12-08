import PyInstaller.__main__
import os

PyInstaller.__main__.run(
    [
        "--name=normcap",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--onedir",
        "--windowed",
        # "-d=all",
        f"--icon={os.path.join('ressource', 'normcap.ico')}",
        f"--paths={os.path.join('.', 'normcap')}",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        os.path.join("normcap", "normcap.py"),
    ]
)
