from . import scan
from .bom import Bom, BomError

def add_license(root, nm, id, data):
    scan._add_license({'root': root, 'license-file': nm, 'license': id}, data)
    return data

def test_add_license():
    assert add_license('.', 'lic', 'MIT', {}) == {'license-file': 'lic', 'license': 'MIT'}
    assert add_license('foo', 'lic', 'MIT', {}) == {'dependencies': [{'root': 'foo', 'license-file': 'lic', 'license': 'MIT'}]}
    assert add_license('foo', 'lic', 'MIT', {'dependencies': [{}]}) == {'dependencies': [{}, {'root': 'foo', 'license-file': 'lic', 'license': 'MIT'}]}

def scan_bom(x, **kwargs):
    try:
        ret = scan.scan_bom(Bom(x, '.'), **kwargs)
    except BomError as err:
        return err
    return ret

def test_scan_bom(tmpdir):
    assert scan_bom({'root': tmpdir.strpath}) == None


def test_scan_bom_missing_license(tmpdir):
    assert scan_bom({'root': tmpdir.strpath}) == None
    lic = tmpdir.join('LICENSE.txt')
    lic.write('')

    msg = "Undeclared license file 'LICENSE.txt' in directory '{}'".format(tmpdir.strpath)
    assert scan_bom({'root': tmpdir.strpath}).msg == msg


_mit_license_text = """
MIT License
Copyright (c) <year> <copyright holders>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

def test_scan_bom_missing_license_any_name(tmpdir):
    lic = tmpdir.join('foo.txt')
    lic.write(_mit_license_text)
    msg = "Undeclared MIT license file 'foo.txt' in directory '{}'".format(tmpdir.strpath)
    assert scan_bom({'root': tmpdir.strpath}).msg == msg

def test_scan_bom_missing_license_priority(tmpdir):
    # Complain about files with LICENSE in the name before scanning the rest.
    fooLic = tmpdir.join('foo.txt')
    fooLic.write(_mit_license_text)
    lic = tmpdir.join('LICENSE.md')
    lic.write('')
    msg = "Undeclared license file 'LICENSE.md' in directory '{}'".format(tmpdir.strpath)
    assert scan_bom({'root': tmpdir.strpath}).msg == msg

def test_scan_bom_missing_license_in_directory(tmpdir):
    foss = tmpdir.join('foss')
    foss.mkdir()
    lic = foss.join('LICENSE.txt')
    lic.write('')

    msg = "Undeclared license file 'foss/LICENSE.txt' in directory '{}'".format(tmpdir.strpath)
    assert scan_bom({'root': tmpdir.strpath}).msg == msg

    assert scan_bom({'root': tmpdir.strpath}, add_declarations=True) == {
        'root': tmpdir.strpath,
        'dependencies': [{'root': 'foss', 'license': 'Unknown', 'license-file': 'LICENSE.txt'}]
    }

def test_scan_bom_missing_license_with_declared_file(tmpdir):
    lic = tmpdir.join('LICENSE.txt')
    lic.write(_mit_license_text)

    msg = "Undeclared MIT license in license file '{}'".format(lic.strpath)
    assert scan_bom({'root': tmpdir.strpath, 'license-file': 'LICENSE.txt'}).msg == msg

    assert scan_bom({'root': tmpdir.strpath, 'license-file': 'LICENSE.txt'}, add_declarations=True) == {
        'root': tmpdir.strpath, 'license-file': 'LICENSE.txt', 'license': 'MIT'}

def test_scan_bom_license_in_vcs_directory(tmpdir):
    foss = tmpdir.join('.git')
    foss.mkdir()
    lic = foss.join('LICENSE.txt')
    lic.write('')
    assert scan_bom({'root': tmpdir.strpath}) == None

def test_scan_bom_license_in_component(tmpdir):
    top = tmpdir.join('top')
    top.mkdir()
    foss = top.join('foss')
    foss.mkdir()
    lic = foss.join('LICENSE.txt')
    lic.write('')

    assert scan_bom({'root': tmpdir.strpath, 'dependencies': [{'root': 'top/foss', 'license-file': 'LICENSE.txt', 'license': 'Unknown'}]}) == None


def test_scan_bom_missing_license_in_dependency(tmpdir):
    foss = tmpdir.join('foss')
    foss.mkdir()
    lic = foss.join('LICENSE.txt')
    lic.write('')

    msg = "Undeclared license file 'LICENSE.txt' in directory '{}'".format(foss.strpath)
    assert scan_bom({'root': tmpdir.strpath, 'dependencies': [{'root': 'foss'}]}, scan_components=True).msg == msg

    # Use 'development-dependencies' to safely ignore.
    assert scan_bom({'root': tmpdir.strpath, 'development-dependencies': [{'root': 'foss'}]}, scan_components=True) == None

    # Set 'is_source_dist' to scan development dependencies
    data = {'root': tmpdir.strpath, 'development-dependencies': [{'root': 'foss'}]}
    assert scan_bom(data, is_source_dist=True, scan_components=True).msg == msg

def test_scan_bom_add_declarations(tmpdir):
    data = {'root': tmpdir.strpath}
    assert scan_bom(data, add_declarations=True) == data

    # Ensure 'data' is copied
    data['root'] = 'bogus'
    assert data != {'root': tmpdir.strpath}

def _make_dep(license_file, license_id):
    return {'license-file': license_file, 'license': license_id, 'files': [license_file]}

def coalesce_data(xs, num_files=None):
    if num_files is None:
        num_files = len(xs)
    xs = [_make_dep(license_file, license_id) for license_file, license_id in xs]
    return [(x['license-file'], x['license'], x.get('files')) for x in scan._coalesce_data(xs, num_files)]

def test_coalesce_data(tmpdir):
    assert coalesce_data([]) == []
    assert coalesce_data([('a.txt', 'MIT')]) == [('a.txt', 'MIT', None)]

    # Declare files if only some have license text and not named 'LICENSE'
    assert coalesce_data([('a.txt', 'MIT')], num_files=2) == [('a.txt', 'MIT', ['a.txt'])]
    assert coalesce_data([('LICENSE.txt', 'MIT')], num_files=2) == [('LICENSE.txt', 'MIT', None)]

    # Fold matches under 'LICENSE'
    assert coalesce_data([
        ('a.txt', 'MIT'),
        ('LICENSE', 'MIT'),
    ]) == [
        ('LICENSE', 'MIT', None)
    ]

    # Ensure 'LICENSE' is the default.
    assert coalesce_data([
        ('a.txt', 'MIT'),
        ('LICENSE', 'BSD'),
    ]) == [
        ('LICENSE', 'BSD', None),
        ('a.txt', 'MIT', ['a.txt']),
    ]

    # Dual licensing, no big deal.
    assert coalesce_data([
        ('LICENSE-MIT', 'MIT'),
        ('LICENSE-BSD', 'BSD'),
        ('b.txt', 'BSD'),
    ]) == [
        ('LICENSE-BSD', 'BSD', ['LICENSE-BSD', 'b.txt']),
        ('LICENSE-MIT', 'MIT', ['LICENSE-MIT']),
    ]

    # Merge 'files' of otherwise matching licenses.
    assert coalesce_data([
        ('a.txt', 'MIT'),
        ('LICENSE', 'BSD'),
        ('b.txt', 'MIT'),
    ]) == [
        ('LICENSE', 'BSD', None),
        ('a.txt', 'MIT', ['a.txt', 'b.txt']),
    ]


def test_check_for_licenses(tmpdir):
    assert scan.check_for_licenses(tmpdir.strpath, '.', [], coalesce='none') == []

