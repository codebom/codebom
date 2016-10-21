from . import _version

def test_version():
    assert type(_version.__version__) == str
