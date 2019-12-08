import PyInstaller.__main__
import os

PyInstaller.__main__.run(
    [
        "--name=normcap",
        "--clean",
        "--noconfirm",
        # "--onefile",
        "--onedir",
        "--windowed",
        # "-d=all",
        f"--icon={os.path.join('ressource', 'normcap.ico')}",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        os.path.join("normcap", "normcap.py"),
    ]
)
