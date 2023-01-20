from importlib import resources as importlib_resources
from pathlib import Path
from xml.etree import ElementTree

from PySide6 import QtGui

from normcap.gui import resources


def test_resources_complete(qtbot):
    icons_path = Path(importlib_resources.files("normcap.resources")) / "icons"
    icons_files = [f.name for f in icons_path.glob("*.svg")]

    assert resources.qt_resource_data
    assert resources.qt_resource_name
    assert resources.qt_resource_struct

    tree = ElementTree.parse(icons_path / "resources.qrc")
    root = tree.getroot()
    icons_qrc = [el.text for el in root.find("qresource").findall("file")]

    assert set(icons_qrc) == set(icons_files)

    for icon in icons_qrc:
        stem = icon.split(".")[0]
        assert QtGui.QIcon(f":{stem}").availableSizes(), stem
