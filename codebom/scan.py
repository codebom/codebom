import os
import os.path
import multiprocessing
from contextlib import closing
from .bom import BomError
from .licenseidentifier import identify_license
from .licenses import license_ids
from ruamel.yaml.comments import CommentedMap
import copy

def _get_roots(bom):
    """
    Return a list of 'root' paths from all dependencies.
    """
    roots = [bom.root_dir]

    for dep in bom.all_dependencies:
        roots += _get_roots(dep)

    return roots

def _coalesce_data(deps, num_files):
    if not deps:
        return deps

    default_dep = None

    # Use the 'LICENSE' file as a default, if it exists
    for dep in deps:
        if _license_is_filename(dep['license-file']):
            default_dep = dep
            del default_dep['files']
            break

    new_deps = {}
    for dep in deps:
        license_id = dep['license']

        if dep == default_dep:
            continue

        # No need to declare files with the same license as the license file.
        if default_dep and license_id == default_dep['license']:
            continue

        # Merge file into declaration with matching license.
        if license_id in new_deps:
            licensed_dep = new_deps[license_id]
            licensed_dep['files'] += dep.get('files', [])
        else:
            new_deps[license_id] = dep

    new_deps_list = [new_deps[id] for id in sorted(new_deps)]

    # No need to declare files if all are under the same license.
    if len(new_deps_list) == 1 and len(new_deps_list[0]['files']) == num_files:
        del new_deps_list[0]['files']

    if default_dep:
        new_deps_list.insert(0, default_dep)

    return new_deps_list


_MATCH_THRESHOLD = 0.9

def check_for_licenses(root_dir, curr_dir, files, coalesce):
    """
    Return a list of dependencies with detected licenses for the given files.
    If the filename is 'LICENSE', it will always be included, regardless if
    a particular license is found within it.
    """
    new_deps = []
    for name in files:
        p = os.path.relpath(os.path.join(curr_dir, name), root_dir)
        license_id, confidence = identify_license(os.path.join(root_dir, p), license_ids)
        if _license_is_filename(name) or confidence >= _MATCH_THRESHOLD:
            license_id = confidence >= _MATCH_THRESHOLD and license_id or 'Unknown'
            dep = CommentedMap()
            dep['root'] = os.path.relpath(curr_dir, root_dir)
            dep['license-file'] = name
            dep['license'] = license_id
            dep['files'] = [name]
            new_deps.append(dep)

    if coalesce == 'none':
        return new_deps

    return _coalesce_data(new_deps, len(files))

def _license_is_filename(x):
    """
    Return True if the lowercase version of the filename is 'license'
    """
    return os.path.splitext(x)[0].lower() == 'license'

def _should_walk(x, root_dir, curr_dir, subroots):
    """
    Return True if this is a directory we should check for licenses
    """
    if x in ['.git']:
        # Don't scan version control directories.
        return False

    return os.path.relpath(os.path.join(curr_dir, x), root_dir) not in subroots


class SyncResult(object):
    """Mimic the interface of multiprocessing.pool.AsyncResult"""
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

def apply_sync(f, args):
    """Behave like multiprocessing.pool.apply_async, but run synchronously"""
    return SyncResult(f(*args))

def walk_for_license(root_dir, subroots, coalesce, run_in_parallel):
    """
    Return None if no license files are found. Otherwise, raise an exception.
    """
    new_deps = []
    with closing(multiprocessing.Pool()) as pool:
        apply_func = run_in_parallel and pool.apply_async or apply_sync
        results = []
        for curr_dir, dirs, files in os.walk(root_dir):
            result = apply_func(check_for_licenses, [root_dir, curr_dir, files, coalesce])
            results.append(result)

            # Don't walk dependency directories.
            dirs[:] = [x for x in dirs if _should_walk(x, root_dir, curr_dir, subroots)]

        for result in results:
            new_deps += result.get()

    return new_deps

def _add_license(dep, data):
    if dep['root'] == '.':
        data['license-file'] = dep['license-file']
        data['license'] = dep['license']
    else:
        if 'dependencies' not in data:
            data['dependencies'] = []

        deps = data['dependencies']
        deps.append(dep)

def scan_bom(bom, **kwargs):
    """
    Return None if no missing declarations are discovered. Otherwise raise an
    exception.
    """
    roots = _get_roots(bom)
    is_source_dist = kwargs.get('is_source_dist')
    scan_components = kwargs.get('scan_components')
    add_declarations = kwargs.get('add_declarations')
    coalesce = kwargs.get('coalesce')
    run_in_parallel = kwargs.get('run_in_parallel', False)

    scanned_data = copy.deepcopy(bom.data)

    root_dir = bom.root_dir
    if bom.license_file is None:
        subroots = [os.path.relpath(x, root_dir) for x in roots if x != root_dir]
        pos = 'root' in bom.data and bom.get_key_position('root') or bom.file_position
        new_deps = walk_for_license(root_dir, subroots, coalesce, run_in_parallel)

        if add_declarations:
            for dep in new_deps:
                _add_license(dep, scanned_data)
        elif new_deps:
            dep = new_deps[0]
            license_id = dep['license']
            license_id_str = license_id != 'Unknown' and license_id + ' ' or ''
            p = os.path.normpath(os.path.join(dep['root'], dep['license-file']))
            normRoot = os.path.normpath(root_dir)
            raise BomError("Undeclared {}license file '{}' in directory '{}'".format(license_id_str, p, normRoot), pos)
    else:
        licenseFile = bom.license_file
        if bom.license is None:
            license_id, confidence = identify_license(licenseFile, license_ids)
            pos = bom.get_key_position('license-file')
            license_id_str = confidence >= _MATCH_THRESHOLD and license_id + ' ' or ''
            if add_declarations:
                scanned_data['license'] = confidence >= _MATCH_THRESHOLD and license_id or 'Unknown'
            else:
                raise BomError("Undeclared {}license in license file '{}'".format(license_id_str, licenseFile), pos)

    deps = is_source_dist and bom.all_dependencies or bom.dependencies
    for dep in deps:
        if scan_components or dep.base_dir == bom.base_dir:
            scan_bom(dep, **kwargs)

    if add_declarations:
        return scanned_data
