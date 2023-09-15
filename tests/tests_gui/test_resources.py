from importlib import resources as importlib_resources
from pathlib import Path
from xml.etree import ElementTree

from PySide6 import QtGui

from normcap.gui import resources


def test_resources_complete(qtbot):
    icons_path = Path(importlib_resources.files("normcap.resources")) / "icons"
    icon_files = [f.name for f in icons_path.glob("*.png")]

    assert resources.qt_resource_data
    assert resources.qt_resource_name
    assert resources.qt_resource_struct

    tree = ElementTree.parse(icons_path / "resources.qrc")  # noqa: S314
    root = tree.getroot()
    icons_qrc = [el.text for el in root.find("qresource").findall("file")]

    assert set(icons_qrc) == set(icon_files)

    for icon in icons_qrc:
        stem = icon.split(".")[0]
        assert QtGui.QIcon(f":{stem}").availableSizes(), stem


def test_cleanup_resources():
    resources.qCleanupResources()
    resources.qInitResources()


def test_resources_png_and_svg_exist_for_all_icons(qtbot):
    icons_path = Path(importlib_resources.files("normcap.resources")) / "icons"
    source_icons_path = (
        Path(importlib_resources.files("normcap")).parent
        / "assets"
        / "resources"
        / "icons"
    )
    icon_names_svg = [f.stem for f in source_icons_path.glob("*.svg")]
    icon_names_png = [f.stem for f in icons_path.glob("*.png")]

    assert set(icon_names_png) == set(icon_names_svg)


def test_all_icon_can_be_loaded(qapp):
    icons_path = Path(importlib_resources.files("normcap.resources")) / "icons"
    icon_names = [f.stem for f in icons_path.glob("*.png")]

    for icon in icon_names:
        qicon = QtGui.QIcon(f":{icon}")
        assert qicon
        assert len(qicon.availableSizes()) >= 1
