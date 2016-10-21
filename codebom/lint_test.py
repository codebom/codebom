from . import lint
from .bom import Bom, BomError
import os.path
import io

def lint_bom(data):
    try:
        bom = Bom(data, '.')
        return lint.lint_bom(bom).data
    except BomError as err:
        return err

def test_lint_bom():
    assert lint_bom({'bogus': ''}).msg == "Unexpected field 'bogus'"

    assert lint_bom({'bogus': ''}).msg == "Unexpected field 'bogus'"
    assert lint_bom({}) == {}

def test_lint_bom_license():
    assert lint_bom({'license': 1}).msg == "Expected type 'str', but got 'int'"
    assert lint_bom({'license': 'bogus'}).msg == "Unrecognized license ID 'bogus'"
    assert lint_bom({'license': 'mit'}).msg == "Unrecognized license ID 'mit'. Did you mean 'MIT'?"
    assert lint_bom({'license': 'MIT'}) is not None

def test_lint_bom_origin():
    assert lint_bom({'origin': 1}).msg == "Expected type 'str', but got 'int'"
    assert lint_bom({'origin': 0}).msg == "Expected type 'str', but got 'int'"
    assert lint_bom({'origin': 'https://www.google.com'}) is not None

def test_lint_bom_dependencies():
    assert lint_bom({'dependencies': ''}).msg == "Expected type 'list', but got 'str'"
    assert lint_bom({'dependencies': [1]}).msg == "Expected type 'dict', but got 'int'"
    assert lint_bom({'dependencies': []}) is not None
    assert lint_bom({'dependencies': [{}]}) is not None

def test_lint_bom_dev_dependencies():
    assert lint_bom({'development-dependencies': ''}).msg == "Expected type 'list', but got 'str'"
    assert lint_bom({'development-dependencies': [1]}).msg == "Expected type 'dict', but got 'int'"
    assert lint_bom({'development-dependencies': [{}]}) is not None

def test_lint_bom_dev_dependencies_str(tmpdir):
    # A string is expanded to {'root': str}
    mydir = tmpdir.mkdir('dir')
    bom = Bom({'root': tmpdir.strpath, 'development-dependencies': ['dir']}, '.')
    assert lint.lint_bom(bom).development_dependencies[0].root_dir == mydir.strpath

def test_lint_bom_name():
    assert lint_bom({'name': 'foo'}) == {'name': 'foo'}
    assert lint_bom({'name': 'foo', 'dependencies': [{'name': 'foo', 'license': 'MIT'}]}).msg == "Name 'foo' already defined"

def test_lint_bom_component(tmpdir):
    assert lint_bom({'dependencies': ['bogus-bom.yaml']}).msg == "BOM file not found at './bogus-bom.yaml'"
    assert lint_bom({'dependencies': ['bogus']}).msg == "Directory 'bogus' not found"

    foo_dir = tmpdir.mkdir('foo')
    bom_file = foo_dir.join('.bom.yaml')
    bom_file.write('')

    assert Bom({'dependencies': [foo_dir.strpath]}, foo_dir.strpath).dependencies[0].root_dir == foo_dir.strpath
    assert Bom({'dependencies': [bom_file.strpath]}, foo_dir.strpath).dependencies[0].root_dir == foo_dir.strpath

def test_lint_bom_component_rel(tmpdir):
    # Ensure the component BOM is interpreted from the nested directory.
    foo_dir = tmpdir.mkdir('foo')
    bom_file = foo_dir.join('.bom.yaml')
    bom_file.write('license-file: lic')
    lic = foo_dir.join('lic')
    lic.write('')
    assert lint_bom({'root': foo_dir.strpath}) is not None

def test_lint_bom_root():
    assert lint_bom({'root': 'bogus'}).msg == "Directory 'bogus' not found"
    assert lint_bom({'root': 1}).msg == "Expected type 'str', but got 'int'"
    assert lint_bom({'root': ''}) is not None

def test_lint_bom_files():
    assert lint_bom({'files': ['bogus']}).msg == "File './bogus' not found"

def test_lint_bom_license_file(tmpdir):
    assert lint_bom({'license-file': 1}).msg == "Expected type 'str', but got 'int'"

    msg = "License file 'bogus' not found in directory '{}'".format(tmpdir.strpath)
    assert lint_bom({'root': tmpdir.strpath, 'license-file': 'bogus'}).msg == msg

    # license-file needs to be a file, not a directory.
    tmpdir.mkdir('dir')
    msg = "License file 'dir' not found in directory '{}'".format(tmpdir.strpath)
    assert lint_bom({'root': tmpdir.strpath, 'license-file': 'dir'}).msg == msg

def test_load_linted_bom():
    assert lint.load_linted_bom(io.StringIO(u''), '<stdin>').data == {}
