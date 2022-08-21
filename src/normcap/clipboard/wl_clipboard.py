import subprocess


def copy(text):
    """Use wl-clipboard package to copy text to system clipboard."""
    subprocess.run(
        "wl-copy",
        shell=False,
        input=text,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
