from .bom import BomError, get_item_position, get_file_position
from .licenseconflict import is_dependent_license_compatible

def collect_license_warnings(bom, is_source_dist):
    warnings = []
    license_id = bom.license or 'Unknown'

    deps = is_source_dist and bom.all_dependencies or bom.dependencies
    for dep in deps:
        warnings += collect_license_warnings(dep, is_source_dist)

        dep_license_id = dep.license or 'Unknown'
        if not is_dependent_license_compatible(bom, dep):
            license_conflict_templ = "The license '{}' may be incompatible with the license '{}' in '{}'."
            msg = license_conflict_templ.format(license_id, dep_license_id, dep.root_dir)
            msg += " Specify 'copyright-holders' and/or 'licensees' to state the license is authorized in this context."
            if not is_source_dist:
                msg += " If this dependency is used only for development, move it to the 'development-dependencies' section."
            warnings.append(msg)
    return warnings

def add_source_position(msg, pos):
    return "{}:{}:{}: {}".format(pos.src, pos.line, pos.col, msg) if pos else msg

def analyze_bom(bom, **kwargs):
    """
    The textual counterpart to the graph command.
    """
    warnings = collect_license_warnings(bom, kwargs.get('is_source_dist'))
    pos = 'license' in bom.data and bom.get_value_position('license') or get_file_position(bom.data)
    return [add_source_position(msg, pos) for msg in warnings]
