"""NormCap Package."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("normcap")
except PackageNotFoundError:
    __version__ = "unknown"

app_id = "com.github.dynobo.normcap"
if os.environ.get("NORMCAP_DEV"):
    # This alternative app id is meant for normcap developers only. It allows to
    # setup two different NormCap versions (e.g. a stable one mand one for development)
    # with different .desktop laucherns, which both can ask for permission to talk to
    # DBus Portal.
    app_id += "_dev"
