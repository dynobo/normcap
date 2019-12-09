import PyInstaller.__main__
import os

# import normcap

# print(normcap.__version__)
# exit()

PyInstaller.__main__.run(
    [
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
        # "--hidden-import=tkinter",
        # "--hidden-import=mss",
        # "--hidden-import=pyperclip",
        # "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        "--add-data=/etc/fonts:fonts",
        "--runtime-hook=rthook.py",
        os.path.join("normcap", "__main__.py"),
    ]
)
