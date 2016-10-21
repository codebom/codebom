from .bom import Bom, BomError, load_yaml, SourcePosition, get_file_position, get_value_position, get_key_position, get_item_position, load_bom
from ruamel.yaml.comments import CommentedMap
import pytest
import io

def test_source_position():
    assert SourcePosition(1, 4) == SourcePosition(1, 4)
    assert repr(SourcePosition(1, 4)) == 'SourcePosition(1, 4)'

def test_get_file_position():
    assert get_file_position(load_yaml('a: b', 'foo')) == SourcePosition(1, 1, 'foo')

def test_get_value_position():
    assert get_value_position(load_yaml('a: b', 'foo'), 'a') == SourcePosition(1, 4, 'foo')

def test_get_key_position():
    assert get_key_position(load_yaml('a: b', 'foo'), 'a') == SourcePosition(1, 1, 'foo')

def test_get_item_position():
    assert get_item_position(load_yaml('- a', 'foo'), 0) == SourcePosition(1, 3, 'foo')

def _get_name(data):
    return Bom(data, '.').name

def test_get_name():
    assert _get_name({'name': 'a'}) == 'a'
    assert _get_name({'origin': 'a.tar.gz'}) == 'a.tar.gz'
    assert _get_name({'root': 'a.tar.gz'}) == 'a.tar.gz'
    assert _get_name({'origin': 'a', 'root': 'b'}) == 'a'

def test_files():
    assert Bom({}, '.').files == None
    assert Bom({'files': []}, '.').files == []
    assert Bom({'files': ['a']}, '.').files == ['a']
    assert Bom({'root': 'foo', 'files': ['a']}, '.').files == ['foo/a']

def test_load_bom():
    with pytest.raises(BomError):
        load_bom(io.StringIO(u'['), '<stdin>')

    assert load_bom(io.StringIO(u''), '<stdin>').data == {}
