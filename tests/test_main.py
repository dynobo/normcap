from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

from normcap import app


def test_main_starts_normcap(monkeypatch):
    called = False

    def mocked_app_main():
        nonlocal called
        called = True

    monkeypatch.setattr(app, "run", mocked_app_main)
    main_module = str(
        (Path(__file__).parent.parent / "normcap" / "__main__.py").absolute()
    )
    loader = SourceFileLoader("__main__", main_module)
    spec = spec_from_loader(loader.name, loader)
    assert spec

    loader.exec_module(module_from_spec(spec))
    assert called
