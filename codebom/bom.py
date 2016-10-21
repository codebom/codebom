from ruamel import yaml
from ruamel.yaml.comments import CommentedMap
import os.path

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

class SourcePosition(object):
    def __init__(self, line, col, src=None):
        self.line = line
        self.col = col
        self.src = src

    def __eq__(self, that):
        return self.line == that.line and self.col == that.col and self.src == that.src

    def __repr__(self):
        return 'SourcePosition({}, {})'.format(self.line, self.col)

class BomError(Exception):
    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

class Bom(object):
    def __init__(self, data, base_dir):
        self.data = data
        self.base_dir = base_dir

        deps = data.get('dependencies', [])
        self.dependencies = [_create_bom(x, get_item_position(deps, i), self.root_dir) for i, x in enumerate(deps)]

        deps = data.get('development-dependencies', [])
        self.development_dependencies = [_create_bom(x, get_item_position(deps, i), self.root_dir) for i, x in enumerate(deps)]

    @property
    def root_dir(self):
        p = os.path.join(self.base_dir, self.data.get('root', '.'))
        return os.path.normpath(p)

    @property
    def files(self):
        files = self.data.get('files')
        if not files:
            return files

        return [os.path.normpath(os.path.join(self.root_dir, x)) for x in files]

    @property
    def all_dependencies(self):
        return self.dependencies + self.development_dependencies

    @property
    def origin(self):
        return self.data.get('origin')

    @property
    def name(self):
        nm = self.data.get('name')
        if nm:
            return nm

        origin = self.origin
        path = origin and urlparse(origin).path or self.root_dir
        return os.path.basename(path)

    @property
    def copyright_holders(self):
        return self.data.get('copyright-holders', [])

    @property
    def license_file(self):
        license_file = self.data.get('license-file')
        return license_file and os.path.join(self.root_dir, license_file)

    @property
    def license(self):
        return self.data.get('license')

    @property
    def potential_license_conflicts(self):
        return self.data.get('potential-license-conflicts', [])

    @property
    def root_matches_origin(self):
        return self.data.get('root-matches-origin')

    @property
    def licensees(self):
        return self.data.get('licensees', [])

    @property
    def file_position(self):
        """
        Return the source position of the top of the file, otherwise None.
        """
        return get_file_position(self.data)

    def get_value_position(self, key):
        """
        Return the source position of the value at 'key', otherwise None.
        """
        return get_value_position(self.data, key)

    def get_key_position(self, key):
        """
        Return the source position of 'key', otherwise None.
        """
        return get_key_position(self.data, key)


def annotate_with_source(data, path):
    """
    Return the given list or dictionary, but with an additional
    'src' attribute on its LineCol object.
    """
    if hasattr(data, 'lc'):
        setattr(data.lc, 'src', path)
        if isinstance(data, dict):
            for key, val in data.items():
               data[key] = annotate_with_source(val, path)
        elif isinstance(data, list):
            for idx, val in enumerate(data):
               data[idx] = annotate_with_source(val, path)
    return data

def load_yaml(hdl, path='<stdin>'):
    """
    Return the YAML file in 'hdl' after annotating its metadata with 'path'.
    """
    data = yaml.load(hdl, Loader=yaml.RoundTripLoader)
    return annotate_with_source(data, path)

def get_file_position(data):
    """
    Return the source position of the top of the file, otherwise None.
    """
    pos = getattr(data, 'lc', None)
    if pos:
        return SourcePosition(1, 1, pos.src)

def get_value_position(data, key):
    """
    Return the source position of the value at 'key', otherwise None.
    """
    pos = getattr(data, 'lc', None)
    if pos:
        line, col = pos.value(key)
        return SourcePosition(line + 1, col + 1, pos.src)

def get_key_position(data, key):
    """
    Return the source position of 'key', otherwise None.
    """
    pos = getattr(data, 'lc', None)
    if pos:
        line, col = pos.key(key)
        return SourcePosition(line + 1, col + 1, pos.src)

def get_item_position(xs, idx):
    """
    Return the source position of item 'idx', otherwise None.
    """
    pos = getattr(xs, 'lc', None)
    if pos:
        line, col = pos.item(idx)
        return SourcePosition(line + 1, col + 1, pos.src)

def _find_bom_file(bom_path, pos):
    if os.path.splitext(bom_path)[1] == '.yaml':
        if not os.path.isfile(bom_path):
            raise BomError("BOM file not found at '{}'".format(bom_path), pos)
        return bom_path

    bom_path = os.path.join(bom_path, '.bom.yaml')
    if os.path.isfile(bom_path):
        return bom_path

def load_bom(hdl, path):
    """
    Return the Bill of Materials in 'hdl' and annotate the returned dictionary
    with the source filepath at 'path'.
    """
    try:
        data = load_yaml(hdl, path) or annotate_with_source(CommentedMap(), path)
        return Bom(data, os.path.dirname(path))
    except yaml.parser_.ParserError as e:
        mark = e.problem_mark
        pos = SourcePosition(mark.line + 1, mark.column + 1, mark.name)
        raise BomError('{}, {}'.format(e.context, e.problem), pos)

def _create_bom(data, pos, base_dir):
    if isinstance(data, str):
        bom_path = os.path.join(base_dir, data)
        bom_path = _find_bom_file(bom_path, pos)
        if bom_path:
            with open(bom_path) as hdl:
                return load_bom(hdl, bom_path)
        data = {'root': data}
    if isinstance(data, dict):
        return Bom(data, base_dir)
    raise BomError("Expected type 'dict', but got '{}'".format(type(data).__name__), pos)
