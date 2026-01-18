import brault

def test_import():
    assert brault is not None

def test_version():
    assert hasattr(brault, "__version__")
    assert isinstance(brault.__version__, str)
