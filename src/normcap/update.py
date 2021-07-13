"""Find new version on github or pypi."""
import json
import urllib.request
from typing import Union

from normcap import __version__
from normcap.logger import logger


def get_newest_github_release():
    """Used for briefcase packaged version."""
    try:
        url = "https://api.github.com/repos/dynobo/normcap/releases"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        latest_release_tag = data[0].tag_name.strip("v")
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Couldn't connect to {url} to check for updates.")
        latest_release_tag = ""
    return latest_release_tag


def get_newest_pypi_release():
    """Used for python package version."""
    try:
        url = "https://pypi.org/pypi/normcap/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        latest_release_tag = data["info"]["version"].strip()
    except Exception:  # pylint: disable=broad-except
        logger.exception(f"Couldn't connect to {url} to check for updates.")
        latest_release_tag = ""
    return latest_release_tag


def get_new_version(packaged: bool = False) -> Union[str, bool]:
    """Check on github or pypi if new release is available."""
    if packaged:
        remote_version = get_newest_github_release()
    else:
        remote_version = get_newest_pypi_release()

    if remote_version in ["", __version__]:
        logger.debug("No new version found.")
        return False

    logger.debug(f"New version {remote_version} found.")
    return remote_version
