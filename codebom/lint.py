try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import os.path
from .bom import load_bom, get_file_position, get_value_position, get_key_position, get_item_position, BomError
from .licenses import license_ids

_bom_spec = {
    'root': str,
    'files': list,
    'name': str,
    'license': str,
    'license-file': str,
    'licensees': list,
    'copyright-holders': list,
    'development-dependencies': list,
    'dependencies': list,
    'origin': str,
    'root-matches-origin': bool,
}

valid_licenses = license_ids + [
    'AllRightsReserved',
    'PublicDomain',
    'Unknown',
]

def _typecheck_value(x, ty, pos):
    """
    Raise an error if 'x' is not an instance of type 'ty'.
    """
    if not isinstance(x, ty):
        raise BomError("Expected type '{}', but got '{}'".format(ty.__name__, type(x).__name__), pos)

def _typecheck_dict(d, spec, pos):
    """
    Raise an error of the first field in 'd' that fails to typecheck
    against specification 'spec'.
    """
    _typecheck_value(d, dict, pos)

    for key, val in d.items():
        if key not in spec:
            pos = get_key_position(d, key)
            raise BomError("Unexpected field '{}'".format(key), pos)

        pos = get_value_position(d, key)
        _typecheck_value(val, spec[key], pos)

_names = set()

def lint_bom(bom):
    """
    Return a recursively linted dependency.
    """
    data = bom.data
    _typecheck_dict(data, _bom_spec, get_file_position(data))

    key = 'name'
    name = data.get(key)
    if name:
        if name in _names:
            pos = get_value_position(data, key)
            raise BomError("Name '{}' already defined".format(name), pos)
        _names.add(name)

    root_dir = bom.root_dir

    if not os.path.isdir(root_dir):
        pos = get_value_position(data, 'root')
        raise BomError("Directory '{}' not found".format(root_dir), pos)

    files = data.get('files')
    if files:
        for i, relpath in enumerate(files):
            path = os.path.join(bom.root_dir, relpath)
            if not os.path.isfile(path):
                pos = get_item_position(files, i)
                raise BomError("File '{}' not found".format(path), pos)

    key = 'license-file'
    license_file = data.get(key)
    if license_file:
        path = os.path.join(root_dir, license_file)
        if not os.path.isfile(path):
            msg = "License file '{}' not found in directory '{}'".format(license_file, root_dir)
            pos = get_value_position(data, key)
            raise BomError(msg, pos)

    key = 'license'
    license = data.get(key)
    if license is not None and license not in valid_licenses:
        pos = get_value_position(data, key)
        corrected = next((s for s in valid_licenses if s.lower() == license.lower()), '')
        hint = corrected and ". Did you mean '{}'?".format(corrected) or ''
        raise BomError("Unrecognized license ID '{}'{}".format(license, hint), pos)

    origin = data.get('origin')
    if origin is not None:
        urlparse(origin)

    for x in bom.all_dependencies:
        lint_bom(x)

    return bom

def load_linted_bom(hdl, path):
    """
    Return the loaded, linted BOM in 'hdl'.
    """
    bom = load_bom(hdl, path)
    return lint_bom(bom)

