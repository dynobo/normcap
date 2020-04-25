"""Handler responsible for attaching screenshot(s) to session data."""

# TODO: Cleanup when mss added support for Wayland
# Issue: https://github.com/BoboTiG/python-mss/issues/155
# To be removed:
#  - pyscreenshot
#  - _take_screenshot_alternative()
#  - _get_monitor_infos()
#  - _test_for_wayland()
# To be refactored:
#  - handle()

# Standard
import os
import subprocess

# Extra
import mss  # type: ignore
from PIL import Image  # type: ignore
import pyscreenshot as ImageGrab  # type:ignore

# Own
from normcap.common.data_model import NormcapData
from normcap.handlers.abstract_handler import AbstractHandler


class CaptureHandler(AbstractHandler):
    def handle(self, request: NormcapData) -> NormcapData:
        """Take multimon screenshots and add those images to session data.

        Arguments:
            AbstractHandler {class} -- self
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- Enriched NormCap's session data
        """
        self._logger.info("Taking Screenshot(s)...")

        if not request.test_mode:
            if not self._test_for_wayland():
                request = self._take_screenshot(request)
            else:
                request = self._take_screenshot_alternative(request)
        else:
            self._logger.info("Test mode. Using existing screenshot...")

        if self._next_handler:
            return super().handle(request)
        else:
            return request

    def _take_screenshot(self, request):
        with mss.mss() as sct:
            # Grab screens of all monitors
            for idx, position in enumerate(sct.monitors[1:]):

                raw = sct.grab(position)

                # Convert to Pil
                img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

                # Append list with screenshots
                shot = {"monitor": idx, "image": img, "position": position}
                request.shots.append(shot)

        self._logger.debug("Dataclass after screenshot added:%s", request)

        return request

    def _test_for_wayland(self):
        """Check if we are running on Wayland DE.

        Returns:
            [bool] -- {True} if probably Wayland

        """
        result = False
        if "WAYLAND_DISPLAY" in os.environ:
            self._logger.info(
                "Wayland DE detected. Falling back to alternative screenshot approach..."
            )
            result = True
        return result

    def _take_screenshot_alternative(self, request):
        """Alternative way to take screenshot.

        This is based on pyscreenshot and currrently uses `gnome-screenshot` for capturing.
        It works on linux with `gnome-screenshot` installed, especially on Wayland.
        `xrandr` is used to retrieve information regarding multi monitor setup.

        Arguments:
            request {NormcapData} -- NormCap's session data

        Returns:
            NormcapData -- NormCap's session data with screenshots added

        """

        img_complete = ImageGrab.grab(backend="gnome-screenshot")
        monitors = self._get_monitor_infos()
        for idx, position in enumerate(monitors):
            img = img_complete.crop(
                (
                    position["left"],
                    position["top"],
                    position["left"] + position["width"],
                    position["top"] + position["height"],
                )
            )
            shot = {"monitor": idx, "image": img, "position": position}
            request.shots.append(shot)

        return request

    def _get_monitor_infos(self):
        """Retrieve monitor positions and dimensions using xrandr.

        DEMO OUTPUTS of `xrandr --listactivemonitors`:

        -- on multi monitor --
        Monitors: 3
        0: +*DP-1-2-2 1920/521x1080/293+1050+270  DP-1-2-2
        1: +DP-1-2-1 1920/510x1080/290+2970+270  DP-1-2-1
        2: +DP-1-2-3 1050/473x1680/297+0+0  DP-1-2-3
        -------------------
        -- on single monitor--
        Monitors: 1
         0: +XWAYLAND0 944/250x997/264+0+0  XWAYLAND0
        -------------------

        Raises:
            ValueError: Raised when xrandr exits with error

        Returns:
            list -- List of position dicts with keys {top, left, width, height}

        """

        # Execute xrandr:
        p = subprocess.Popen(
            "xrandr --listactivemonitors",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        proc_lines = p.stdout.readlines()
        proc_code = p.wait()
        if proc_code != 0:
            raise ValueError(f"xrandr error: {proc_code}\nOutput:{proc_lines}")

        # Parse result
        monitors = []
        for line in proc_lines:
            line = line.decode()

            sections = line.split()
            # 0       1             2             3
            # 0: +*DP-1-2-2 1920/521x1080/293 XWAYLAND0

            # Skip lines containing no monitor info
            if len(sections) < 4:
                continue

            dim_section = sections[2]
            dim = dim_section.split("/")
            #   0      1          2
            # 1920/521x1080/293+1050+270

            pos = dim[2].split("+")
            #  0    1   2
            # 293+1050+270

            position = {
                "width": int(dim[0]),
                "height": int(dim[1].split("x")[1]),
                "left": int(pos[1]),
                "top": int(pos[2]),
            }
            monitors.append(position)

        return monitors
