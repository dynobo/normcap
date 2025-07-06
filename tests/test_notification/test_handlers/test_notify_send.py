import subprocess
import sys
from pathlib import Path

import pytest

from normcap.notification.handlers import notify_send


@pytest.mark.skipif(sys.platform != "linux", reason="Linux specific test")
def test_notify_without_action(monkeypatch):
    # GIVEN a the notify-send handler (and a mocked Popen)

    cmd_args = []

    def popen_decorator(func):
        def decorated_popen(cmd: list[str], **kwargs):
            cmd_args.extend(cmd)
            return func(["echo", "test"], **kwargs)

        return decorated_popen

    monkeypatch.setattr(subprocess, "Popen", popen_decorator(subprocess.Popen))

    # WHEN a notification is send
    result = notify_send.notify(
        title="Title", message="Message", action_label=None, action_callback=None
    )

    # THEN the command that gets executed via Popen should be in the specific format
    assert result is True

    assert cmd_args[0] == "notify-send"
    assert cmd_args[1].startswith("--icon=")
    assert cmd_args[2] == "--app-name=NormCap"
    assert cmd_args[3] == "--transient"
    assert cmd_args[4] == "Title"
    assert cmd_args[5] == "Message"

    icon = cmd_args[1].removeprefix("--icon=")
    assert Path(icon).exists()
