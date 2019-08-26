import PyInstaller.__main__
import os

PyInstaller.__main__.run(
    [
        "--name=%s" % "normcap",
        "--clean",
        "--noconfirm",
        "--onefile",
        # "--onedir",
        "--windowed",
        # "--icon=%s" % os.path.join("ressource", "normcap.ico"),
        "--hidden-import=%s" % "PIL",
        "--hidden-import=%s" % "PIL._imagingtk",
        "--hidden-import=%s" % "PIL._tkinter_finder",
        os.path.join("normcap", "normcap.py"),
    ]
)
