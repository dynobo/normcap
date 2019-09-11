import PyInstaller.__main__
import os

# TODO: Switch based on platform

os.chdir("./normcap")

PyInstaller.__main__.run(
    [
        "--name=normcap",
        "--clean",
        "--noconfirm",
        "-OO",  # Bytecode Optimization
        # "--onefile",
        "--onedir",
        #"--windowed",
        "-D", # debug
        # "--icon=%s" % os.path.join("ressource", "normcap.ico"),
        "--paths=./normcap",
        "--hidden-import=PIL", 
        "--hidden-import=PIL._imagingtk",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=utils.log_dataclass",
        os.path.join("normcap","normcap.py"),
    ]
)
