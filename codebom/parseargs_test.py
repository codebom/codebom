from .parseargs import parse_args, get_default_bom
import pytest
import sys

def test_get_default_bom(tmpdir, monkeypatch):
    assert get_default_bom() == sys.stdin

    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)
    assert get_default_bom() == None

def test_parse_args(tmpdir):
    bom_file = tmpdir.join('.bom.yaml')
    bom_file.write('')
    bom_path = bom_file.strpath

    with pytest.raises(SystemExit): parse_args([])
    with pytest.raises(SystemExit): parse_args(['-f', 'bogus'])
    with pytest.raises(SystemExit): parse_args(['-f', bom_path, '--bogus'])
    with pytest.raises(SystemExit): parse_args(['-f', bom_path, 'bogus'])
    with pytest.raises(SystemExit): parse_args(['--version'])

    assert parse_args(['-f', bom_path, 'verify']).command == 'verify'
    assert parse_args(['-f', bom_path, 'verify']).f.name == bom_path
    assert parse_args(['-f', bom_path, 'verify', '-o', 'foo']).o.name == 'foo'

def test_parse_args_source_distribution(tmpdir):
    assert parse_args(['verify']).source_distribution == False
    assert parse_args(['verify', '--source-distribution']).source_distribution == True
    assert parse_args(['scan', '--source-distribution']).source_distribution == True

def test_parse_args_check_origins(tmpdir):
    assert parse_args(['verify']).check_origins == None
    assert parse_args(['verify', '--check-origins=uri']).check_origins == 'uri'
    assert parse_args(['verify', '--check-origins=contents']).check_origins == 'contents'

def test_parse_args_recurse(tmpdir):
    assert parse_args(['scan']).recursive == False
    assert parse_args(['scan', '--recursive']).recursive == True
    assert parse_args(['scan', '-r']).recursive == True

def test_parse_args_add(tmpdir):
    assert parse_args(['scan']).add == False
    assert parse_args(['scan', '--add']).add == True
    assert parse_args(['scan', '-a']).add == True
    assert parse_args(['scan', '-o', 'foo']).o.name == 'foo'

def test_parse_args_coalesce(tmpdir):
    assert parse_args(['scan']).coalesce == 'all'
    assert parse_args(['scan', '--coalesce=none']).coalesce == 'none'
