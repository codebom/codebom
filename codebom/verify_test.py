from . import verify
from .bom import Bom, BomError, SourcePosition
import shutil
import os.path
import io

def verify_bom(x, **kwargs):
    try:
        verify.verify_bom(Bom(x, '.'), '.', **kwargs)
    except BomError as err:
        return err

def verify_origin_dir(root, origin, files, uri):
    try:
        ret = verify.verify_origin_dir(root, origin, files, uri, None)
    except BomError as err:
        return err
    return ret

def make_file_tree(spec, path):
    if isinstance(spec, str):
        path.write(spec)
    elif isinstance(spec, dict):
        path.mkdir()
        for nm in spec:
            make_file_tree(spec[nm], path.join(nm))

def test_verify_origin_dir_root_has_more(tmpdir):
    foo = tmpdir.join('foo')
    bar = tmpdir.join('bar')

    make_file_tree({'a.c': 'A', 'b.c': 'B'}, foo)
    make_file_tree({'a.c': 'A'}, bar)

    msg = "Directory '{}' does not match the contents of 'http://bar'\n  Only in '{}': ['b.c']".format(foo.strpath, foo.strpath)
    assert verify_origin_dir(foo.strpath, bar.strpath, None, 'http://bar').msg == msg

def test_verify_origin_dir_root_has_less(tmpdir):
    foo = tmpdir.join('foo')
    bar = tmpdir.join('bar')

    make_file_tree({'a.c': 'A'}, foo)
    make_file_tree({'a.c': 'A', 'b.c': 'B'}, bar)

    msg = "Directory '{}' does not match the contents of 'http://bar'\n  Only in 'http://bar': ['b.c']".format(foo.strpath)
    assert verify_origin_dir(foo.strpath, bar.strpath, None, 'http://bar').msg == msg

def test_verify_origin_dir_root_is_different(tmpdir):
    foo = tmpdir.join('foo')
    bar = tmpdir.join('bar')

    make_file_tree({'a.c': 'A', 'b.c': 'A'}, foo)
    make_file_tree({'a.c': 'A', 'b.c': 'XYZ'}, bar)

    tmpl = """Directory '{}' does not match the contents of 'http://bar'
  In both root and origin, but different contents: ['b.c']
  Add 'root-matches-origin: false' if these files have been modified locally."""

    msg = tmpl.format(foo.strpath)
    assert verify_origin_dir(foo.strpath, bar.strpath, None, 'http://bar').msg == msg
    assert verify_origin_dir(foo.strpath, bar.strpath, ['b.c'], 'http://bar').msg == msg
    assert verify_origin_dir(foo.strpath, bar.strpath, ['a.c'], 'http://bar') is None

def test_verify_origin(tmpdir):
    foo = tmpdir.join('foo')

    make_file_tree({'a.c': 'A', 'b.c': 'B'}, foo)

    foo_dir = foo.strpath

    # Test tar
    tar_path = shutil.make_archive(foo_dir, 'gztar', foo_dir)
    assert verify.verify_origin(foo_dir, tar_path, None, 'http://a.com', None) is None

    # Test zip
    tar_path = shutil.make_archive(foo_dir, 'zip', foo_dir)
    assert verify.verify_origin(foo_dir, tar_path, None, 'http://a.com', None) is None

    # Test fragment URI
    tar_path = shutil.make_archive(foo_dir + '-foo', 'gztar', tmpdir.strpath, 'foo')
    assert verify.verify_origin(foo_dir, tar_path, None, 'http://a.com#foo', None) is None

def test_verify_bom_origin(httpserver):
    httpserver.serve_content('File not found!', 404)
    assert verify_bom({'origin': httpserver.url}, check_origins='uri').msg == "Not found '{}'".format(httpserver.url)

    httpserver.serve_content("I'm feeling lucky")
    assert verify_bom({'origin': httpserver.url}, check_origins='contents').msg == "Unexpected file type at {}. Expected .zip or .tar.gz".format(httpserver.url)
    assert verify_bom({'origin': httpserver.url}, check_origins='uri') is None


def test_verify_bom_origin_contents(tmpdir, httpserver):
    foo = tmpdir.join('foo')
    make_file_tree({'a.c': 'A', 'b.c': 'B'}, foo)
    foo_dir = foo.strpath
    tar_path = shutil.make_archive(foo_dir, 'gztar', foo_dir)

    with io.open(tar_path, 'rb') as hdl:
        contents = hdl.read()

    httpserver.serve_content(contents)
    assert verify_bom({'root': foo_dir, 'origin': httpserver.url}, check_origins='contents') is None


def test_copyright_holders(tmpdir):
    assert verify_bom({'copyright-holders': []}) == None
    assert verify_bom({'copyright-holders': ['a', 'b']}) == None

    # If a license-file is provided, ensure all copyright holders are mentioned.
    badLic = tmpdir.join('bad-lic.txt')
    badLic.write('Copyright A')
    msg = "Copyright holder 'B' not found in license file '{}'".format(badLic.strpath)
    assert verify_bom({'copyright-holders': ['A', 'B'], 'license-file': badLic.strpath}).msg == msg

    goodLic = tmpdir.join('good-lic.txt')
    goodLic.write('Copyright A B')
    assert verify_bom({'copyright-holders': ['A', 'B'], 'license-file': goodLic.strpath}) == None

    # If 'root' is a file, assume it contains a copyright notice.
    assert verify_bom({'copyright-holders': ['A', 'B'], 'root': goodLic.strpath}) == None

def test_verify_bom(httpserver):
    httpserver.serve_content('File not found!', 404)
    assert verify_bom({'dependencies': [{'origin': httpserver.url}]}, check_origins='uri').msg == "Not found '{}'".format(httpserver.url)
    assert verify_bom({'dependencies': []}) == None
    assert verify_bom({'dependencies': [{'license': 'MIT'}]}) == None

def test_verify_bom_dev_dependencies(httpserver):
    httpserver.serve_content('File not found!', 404)
    assert verify_bom(
            {'development-dependencies': [{'origin': httpserver.url}]},
            is_source_dist=True,
            check_origins='uri'
        ).msg == "Not found '{}'".format(httpserver.url)
    assert verify_bom({'development-dependencies': []}) == None
    assert verify_bom({'development-dependencies': [{'root': 'foss'}]}) == None
    assert verify_bom({'development-dependencies': [{'root': 'foss', 'license': 'MIT'}]}, is_source_dist=True) == None

def test_collect_license_warnings():
    def license_warnings(data, is_source_dist=False):
        return verify.collect_license_warnings(Bom(data, '.'), is_source_dist)

    data = {
        'license': 'AllRightsReserved',
        'dependencies': [{'root': 'foss', 'license': 'GPL-3.0'}]
    }
    assert license_warnings(data) == ["The license 'AllRightsReserved' may be incompatible with the license 'GPL-3.0' in 'foss'. Specify 'copyright-holders' and/or 'licensees' to state the license is authorized in this context. If this dependency is used only for development, move it to the 'development-dependencies' section."]

    # Declaring AllRightsReserved is not sufficient. Need copyright-holders too.
    data = {
        'license': 'AllRightsReserved',
        'dependencies': [{'root': 'foss', 'license': 'AllRightsReserved'}]
    }
    assert license_warnings(data) == ["The license 'AllRightsReserved' may be incompatible with the license 'AllRightsReserved' in 'foss'. Specify 'copyright-holders' and/or 'licensees' to state the license is authorized in this context. If this dependency is used only for development, move it to the 'development-dependencies' section."]

    # Use 'licensee' declaration if you are an authorized client.
    data = {
        'license': 'AllRightsReserved',
        'copyright-holders': ['P', 'Q'],
        'dependencies': [{'root': 'foss', 'license': 'GPL-3.0', 'licensees': ['Q', 'R']}]
    }
    assert license_warnings(data) == []

    # Assume copyright-holder is an implicit licensee.
    data = {
        'license': 'AllRightsReserved',
        'copyright-holders': ['Q'],
        'dependencies': [{'root': 'foss', 'license': 'GPL-3.0', 'copyright-holders': ['Q']}]
    }
    assert license_warnings(data) == []

    # Don't warn if conflict happens within a development dependency (unless
    # verifying a source distribution).
    data = {
        'development-dependencies': [
            {'license': 'AllRightsReserved', 'dependencies': [{'license': 'GPL-3.0'}]}
        ]
    }
    assert license_warnings(data) == []

    # Don't warn on known conflicts.
    data = {
        'license': 'AllRightsReserved',
        'copyright-holders': ['Q'],
        'potential-license-conflicts': ['foss'],
        'dependencies': [{'root': 'foss', 'license': 'GPL-3.0'}]
    }
    assert license_warnings(data) == []

def test_warn_if_license_mismatch():
    def license_warnings(data, is_source_dist=False):
        allLicenseIds = ['MIT', 'Apache-1.1', 'Apache-2.0']
        return verify.collect_license_warnings(Bom(data, '.'), is_source_dist, allLicenseIds)

    licenseFile = os.path.join(os.path.dirname(__file__), 'licenses', 'Apache-2.0.txt')
    data = {'license': 'Apache-1.1', 'license-file': licenseFile}
    assert license_warnings(data) == ["License file '{}' declared as Apache-1.1, but it looks more like Apache-2.0.".format(licenseFile)]

    data = {'license': 'Apache-2.0', 'license-file': licenseFile}
    assert license_warnings(data) == []

def test_verify_bom_license_conflict(capsys):
    out = verify_bom({'license': 'AllRightsReserved', 'dependencies': [{'root': 'foss', 'license': 'GPL-3.0'}]})
    assert out.msg.startswith('The license')

def test_verify_bom_output():
    data = {'licensees': ['Q'], 'potential-license-conflicts': ['foo']}
    assert verify.verify_bom(Bom(data, '.'), '.') == data

    data = {'licensees': [], 'potential-license-conflicts': []}
    assert verify.verify_bom(Bom(data, '.'), '.') == {}

    data = {'name': 'foo'}
    assert verify.verify_bom(Bom(data, '.'), '.') == data

    data = {'files': ['foo']}
    assert verify.verify_bom(Bom(data, '.'), '.') == data

    data = {'files': ['foo']}
    assert verify.verify_bom(Bom(data, '.'), 'subdir') == {'root': '..', 'files': ['foo']}

def test_warn(capsys):
    def warn(msg, pos):
        verify.warn(msg, pos)
        return capsys.readouterr()[1]

    assert warn('bar', None) == 'warning: bar\n'
    assert warn('bar', SourcePosition(1, 1, 'foo.c')) == 'foo.c:1:1: warning: bar\n'
