try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

from .bom import BomError, get_item_position, get_file_position
from .licenseconflict import is_dependent_license_compatible
from .licenseidentifier import identify_license
from .licenses import license_ids
from ruamel.yaml.comments import CommentedMap
import os
import os.path
import tempfile
import tarfile
import zipfile
import filecmp
import shutil
import sys

def warn_if_license_mismatch(license_path, license_id, all_license_ids):
    declared_id, declared_percentage = identify_license(license_path, [license_id])

    # Don't guess the license when we don't have a template for the license
    # the user declared.
    if declared_id is None:
        return

    # Don't guess a license when the declared license is a close match.
    if declared_percentage >= 0.9:
        return

    guessed_id, guessed_percentage = identify_license(license_path, all_license_ids)
    if guessed_percentage > declared_percentage:
        return "License file '{}' declared as {}, but it looks more like {}.".format(license_path, license_id, guessed_id)

def collect_license_warnings(bom, is_source_dist, all_license_ids=license_ids):
    warnings = []
    license_id = bom.license or 'Unknown'

    license_file = bom.license_file
    if license_file:
        warning = warn_if_license_mismatch(license_file, license_id, all_license_ids)
        if warning:
            warnings.append(warning)

    known_conflicts = bom.potential_license_conflicts
    deps = is_source_dist and bom.all_dependencies or bom.dependencies
    for dep in deps:
        dep_license_id = dep.license or 'Unknown'
        if not is_dependent_license_compatible(bom, dep):
            if dep.data.get('root') in known_conflicts:
                continue

            license_conflict_templ = "The license '{}' may be incompatible with the license '{}' in '{}'."
            msg = license_conflict_templ.format(license_id, dep_license_id, dep.root_dir)
            msg += " Specify 'copyright-holders' and/or 'licensees' to state the license is authorized in this context."
            if not is_source_dist:
                msg += " If this dependency is used only for development, move it to the 'development-dependencies' section."
            warnings.append(msg)
    return warnings

def warn(msg, pos):
    if pos:
        sys.stderr.write("{}:{}:{}: ".format(pos.src, pos.line, pos.col))
    sys.stderr.write("warning: {}\n".format(msg))

def file_contains(haystack_path, needle):
    """
    Return True if the given 'needle' is in the file at 'haystack_path'.
    """
    with open(haystack_path) as haystack:
        return needle in haystack.read()

def verify_uri(origin, pos):
    """
    Return None if the URI 'origin' is a valid network endpoint. Otherwise
    raise an exception.
    """
    origin_sans_fragment = origin.split('#')[0]
    try:
        urlopen(origin_sans_fragment)
    except:
        raise BomError("Not found '{}'".format(origin_sans_fragment), pos)

def verify_origin_dir(root_dir, originDir, files, originUri, pos):
    """
    Return None if the contents of 'root_dir' match the contents of 'originDir'.
    Otherwise raise an exception.
    """
    uri = urlparse(originUri)
    comp = filecmp.dircmp(root_dir, os.path.join(originDir, uri.fragment))

    if files is not None:
        comp.left_only = [x for x in comp.left_only if x in files]
        comp.right_only = [x for x in comp.right_only if x in files]
        comp.diff_files = [x for x in comp.diff_files if x in files]

    if comp.left_only or comp.right_only or comp.diff_files:
        msg = "Directory '{}' does not match the contents of '{}'".format(root_dir, originUri)
        if comp.left_only:
            msg += "\n  Only in '{}': {}".format(root_dir, comp.left_only)
        if comp.right_only:
            msg += "\n  Only in '{}': {}".format(originUri, comp.right_only)
        if comp.diff_files:
            msg += "\n  In both root and origin, but different contents: {}".format(comp.diff_files)
            msg += "\n  Add 'root-matches-origin: false' if these files have been modified locally."

        raise BomError(msg, pos)

def verify_origin(root_dir, filename, files, origin, pos):
    """
    Return None if the contents of 'root_dir' match the contents of the zipfile or
    tarball at 'filename'.  Otherwise raise an exception.
    """
    if tarfile.is_tarfile(filename):
        tar = tarfile.open(filename)
    elif zipfile.is_zipfile(filename):
        tar = zipfile.ZipFile(filename)
    else:
        raise BomError("Unexpected file type at {}. Expected .zip or .tar.gz".format(origin), pos)

    tmpdir = tempfile.mkdtemp()
    try:
        tar.extractall(tmpdir)
        verify_origin_dir(root_dir, tmpdir, files, origin, pos)
    finally:
        shutil.rmtree(tmpdir)
        tar.close()

def download_and_verify_origin(root_dir, files, origin, pos):
    """
    Return None if the contents of 'root_dir' match the contents of the zipfile or
    tarball at 'origin'.  Otherwise raise an exception.
    """
    origin_sans_fragment = origin.split('#')[0]
    filename, headers = urlretrieve(origin_sans_fragment)
    try:
        verify_origin(root_dir, filename, files, origin, pos)
    finally:
        os.remove(filename)

def _verify_deps(deps, parent_base_dir, **kwargs):
    verified_deps = []
    for idx, dep in enumerate(deps):
        pos = get_item_position(deps, idx)
        verified = verify_bom(dep, parent_base_dir, **kwargs)
        verified_deps.append(verified)
    return verified_deps

def _verify_field(field_name, bom, parent_base_dir, verified_data, **kwargs):
    val = bom.data.get(field_name)
    if field_name == 'name':
        verified_data[field_name] = val
    elif field_name == 'license' and val != None:
        verified_data[field_name] = val
    elif val and field_name in ['files', 'licensees', 'copyright-holders', 'potential-license-conflicts']:
        verified_data[field_name] = val
    elif field_name == 'origin':
        check_origins = kwargs.get('check_origins')
        origin = bom.origin
        if check_origins and origin is not None:
            pos = bom.get_value_position('origin')
            verify_uri(origin, pos)
            verified_data['origin'] = origin
            if check_origins == 'contents':
                rootMatchesOrigin = bom.root_matches_origin
                if rootMatchesOrigin is not False:
                    download_and_verify_origin(bom.root_dir, bom.data.get('files'), origin, pos)
                    rootMatchesOrigin = True

                if rootMatchesOrigin is not None:
                    verified_data['root-matches-origin'] = rootMatchesOrigin
    elif field_name == 'license-file':
        owners = bom.copyright_holders
        license_file = bom.data.get('license-file')
        if license_file:
            license_path = os.path.join(bom.root_dir, license_file)
            for i, owner in enumerate(owners):
                if not file_contains(license_path, owner):
                    pos = get_item_position(owners, i)
                    raise BomError("Copyright holder '{}' not found in license file '{}'".format(owner, license_path), pos)

            verified_data['license-file'] = license_file
    elif field_name == 'dependencies':
        verified_deps = _verify_deps(bom.dependencies, parent_base_dir, **kwargs)
        if verified_deps:
            verified_data['dependencies'] = verified_data.get('dependencies', []) + verified_deps
    elif field_name == 'development-dependencies':
        if kwargs.get('is_source_dist'):
            verified_deps = _verify_deps(bom.development_dependencies, parent_base_dir, **kwargs)
            if verified_deps:
                verified_data['dependencies'] = verified_data.get('dependencies', []) + verified_deps
        else:
            root_dirs = [os.path.relpath(x.root_dir, parent_base_dir) for x in bom.development_dependencies]
            dev_deps = [root for root in root_dirs if root != '.']
            if dev_deps:
                verified_data['development-dependencies'] = dev_deps

def verify_bom(bom, parent_base_dir, **kwargs):
    """
    Return None if the fields in 'bom' are consistent. Otherwise raise an exception.
    """
    verified_data = CommentedMap()

    root_dir = os.path.relpath(bom.root_dir, parent_base_dir)
    if root_dir != '.':
        verified_data['root'] = root_dir
        parent_base_dir = os.path.join(parent_base_dir, root_dir)

    for field_name in bom.data:
        _verify_field(field_name, bom, parent_base_dir, verified_data, **kwargs)

    for msg in collect_license_warnings(bom, kwargs.get('is_source_dist')):
        pos = 'license' in bom.data and bom.get_value_position('license') or get_file_position(bom.data)
        raise BomError(msg, pos)

    return verified_data
