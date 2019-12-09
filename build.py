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
        "--debug=all",
        f"--icon={os.path.join('ressource', 'normcap.ico')}",
        f"--paths={os.path.join('.', 'normcap')}",
        # "--hidden-import=tkinter",
        # "--hidden-import=mss",
        # "--hidden-import=distutils",
        # "--hidden-import=pyperclip",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        # "--add-data=/etc/fonts:fonts",
        # "--runtime-hook=rthook.py",
        os.path.join("normcap", "normcap.py"),
    ]
)
