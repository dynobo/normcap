import argparse
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        sys.path.insert(0, f"{(Path(__file__).parent / 'bundle').resolve()}")
        from l10n import main

        args = argparse.Namespace(update_all=False, create_new=False)
        main(args)
