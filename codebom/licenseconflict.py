import enum

class Restrictiveness(enum.IntEnum):
    permissive = 0
    lessRestrictive = 1
    restrictive = 2
    unknown = 3

_restrictiveness_map = {
    'AFL': Restrictiveness.restrictive,
    'AGPL': Restrictiveness.restrictive,
    'AllRightsReserved': Restrictiveness.restrictive,
    'Artistic': Restrictiveness.restrictive,
    'Apache-1.1': Restrictiveness.permissive,
    'Apache-2.0': Restrictiveness.lessRestrictive,
    'BSL': Restrictiveness.permissive,
    'BSD': Restrictiveness.permissive,
    'CDDL-1.0': Restrictiveness.restrictive,
    'CPOL': Restrictiveness.restrictive,
    'CPL-1.0': Restrictiveness.restrictive,
    'EPL': Restrictiveness.restrictive,
    'EUPL': Restrictiveness.restrictive,
    'GPL': Restrictiveness.restrictive,
    'ISC': Restrictiveness.permissive,
    'LGPL': Restrictiveness.restrictive,
    'MIT': Restrictiveness.permissive,
    'MPL': Restrictiveness.restrictive,
    'OpenSSL': Restrictiveness.permissive,
    'PublicDomain': Restrictiveness.permissive,
    'MS-RL': Restrictiveness.restrictive,
    'RPSL': Restrictiveness.restrictive,
    'SPL': Restrictiveness.restrictive,
    'Unknown': Restrictiveness.unknown,
    'W3C': Restrictiveness.permissive,
    'Zlib': Restrictiveness.permissive,
    'IJG': Restrictiveness.permissive,
}

def _restrictiveness(license_id):
    name = license_id.split('-')[0]
    rst = _restrictiveness_map.get(license_id)
    if rst is None:
        rst = _restrictiveness_map.get(name)
    if rst is None:
        rst = Restrictiveness.unknown
    return rst

def are_licenses_compatible(license_id, dep_license_id):
    """
    Return True if we think the licenses are compatible
    """
    dep_restrictiveness = _restrictiveness(dep_license_id)

    if dep_restrictiveness == Restrictiveness.unknown:
        return False

    if dep_restrictiveness == Restrictiveness.permissive:
        return True

    return dep_license_id == license_id and license_id != 'AllRightsReserved'

def is_dependent_license_compatible(bom, dep):
    """
    Return True if we think the dependent license is compatible
    """
    license_id = bom.license or 'Unknown'
    owners = bom.copyright_holders
    licensees = dep.licensees + dep.copyright_holders

    if any(nm in licensees for nm in owners):
        return True

    dep_license_id = dep.license or 'Unknown'
    return are_licenses_compatible(license_id, dep_license_id)
