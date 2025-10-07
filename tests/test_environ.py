import os
from importlib import resources
from pathlib import Path

from normcap import environment
from normcap.platform import system_info


def test_prepare_env():
    environment.prepare()


def test_set_environ_for_wayland(monkeypatch):
    xcursor_size = os.environ.get("XCURSOR_SIZE", "")
    qt_qpa_platform = os.environ.get("QT_QPA_PLATFORM", "")

    try:
        with monkeypatch.context() as m:
            m.delenv("XCURSOR_SIZE", raising=False)
            m.delenv("QT_QPA_PLATFORM", raising=False)

            environment._set_environ_for_wayland()

            assert os.environ.get("XCURSOR_SIZE") == "24"
            assert os.environ.get("QT_QPA_PLATFORM") == "wayland"
    finally:
        os.environ["XCURSOR_SIZE"] = xcursor_size
        os.environ["QT_QPA_PLATFORM"] = qt_qpa_platform


def test_set_environ_for_appimage(monkeypatch):
    binary_path = str(Path(__file__).resolve().parents[2] / "bin")
    with monkeypatch.context() as m:
        m.setenv("PATH", "/normcap/test")
        environment._set_environ_for_appimage()
        path = os.environ.get("PATH", "")
    assert path.endswith(os.pathsep + binary_path)


def test_set_environ_for_flatpak(monkeypatch):
    with monkeypatch.context() as m:
        test_value = "something"
        m.setenv("LD_PRELOAD", test_value)
        environment._set_environ_for_flatpak()
        assert os.environ.get("LD_PRELOAD") == test_value

        m.setenv("LD_PRELOAD", "nocsd")
        environment._set_environ_for_flatpak()
        assert not os.environ.get("LD_PRELOAD")

        m.delenv("LD_PRELOAD", raising=False)
        environment._set_environ_for_flatpak()
        assert os.environ.get("LD_PRELOAD", None) is None


def test_copy_traineddata_files_briefcase(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        tessdata_path = tmp_path / "tessdata"
        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        # Copying without should copy the temporary traineddata files
        for _ in range(3):
            environment.copy_traineddata_files(target_dir=tessdata_path)

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 2

    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_copy_traineddata_files_flatpak(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    monkeypatch.setattr(environment.system_info, "is_flatpak", lambda: True)
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()
    try:
        tessdata_path = tmp_path / "tessdata"
        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        paths = []

        def mocked_path(path_str: str):
            paths.append(path_str)
            if path_str == "/app/share/tessdata":
                path_str = str(resource_path / "tessdata")
            return Path(path_str)

        monkeypatch.setattr(environment, "Path", mocked_path)
        for _ in range(3):
            environment.copy_traineddata_files(target_dir=tessdata_path)

            traineddatas = list(tessdata_path.glob("*.traineddata"))
            txts = list(tessdata_path.glob("*.txt"))
            assert traineddatas
            assert len(txts) == 2
            assert "/app/share/tessdata" in paths
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()


def test_copy_traineddata_files_not_copying(tmp_path, monkeypatch):
    # Create placeholder for traineddata files, if they don't exist
    with resources.as_file(resources.files("normcap.resources")) as file_path:
        resource_path = Path(file_path)
    (resource_path / "tessdata" / "placeholder_1.traineddata").touch()
    (resource_path / "tessdata" / "placeholder_2.traineddata").touch()

    try:
        tessdata_path = tmp_path / "tessdata"

        # Copying without being flatpak or briefcase should do nothing
        environment.copy_traineddata_files(target_dir=tessdata_path)

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts

        # Copying within package but with target_path=None should do nothing
        monkeypatch.setattr(system_info, "is_briefcase_package", lambda: True)
        environment.copy_traineddata_files(target_dir=None)

        traineddatas = list(tessdata_path.glob("*.traineddata"))
        txts = list(tessdata_path.glob("*.txt"))
        assert not traineddatas
        assert not txts
    finally:
        # Make sure to delete possible placeholder files
        for f in (resource_path / "tessdata").glob("placeholder_?.traineddata"):
            f.unlink()
