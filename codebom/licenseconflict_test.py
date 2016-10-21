from . import licenseconflict as lc

def test_restrictiveness():
    assert lc._restrictiveness('Adobe-Glyph') == lc.Restrictiveness.unknown
    assert lc._restrictiveness('Apache-1.1') == lc.Restrictiveness.permissive
    assert lc._restrictiveness('Apache-2.0') == lc.Restrictiveness.lessRestrictive
    assert lc._restrictiveness('GPL-2.0') == lc.Restrictiveness.restrictive

def test_are_license_compatible():
    # Identical licenses can be folded.
    assert lc.are_licenses_compatible('GPL-2.0', 'GPL-2.0') == True

    # Can't add a restrictive dependency to a package with a permissive license.
    assert lc.are_licenses_compatible('MIT', 'GPL-2.0') == False

    # Can add a permissive dependency to a package with a restrictive license.
    assert lc.are_licenses_compatible('GPL-2.0', 'MIT') == True

    # Giving away the farm?
    assert lc.are_licenses_compatible('AllRightsReserved', 'GPL-3.0') == False

    # IP Leak?
    assert lc.are_licenses_compatible('GPL-3.0', 'AllRightsReserved') == False

    # AllRightsReserved but are copyright-holders the same?
    assert lc.are_licenses_compatible('AllRightsReserved', 'AllRightsReserved') == False

    # No prob.
    assert lc.are_licenses_compatible('AllRightsReserved', 'MIT') == True

    # Sure thing.
    assert lc.are_licenses_compatible('AllRightsReserved', 'PublicDomain') == True

    # Need more information.
    unknownLic = 'Adobe-Glyph'
    assert lc._restrictiveness(unknownLic) == lc.Restrictiveness.unknown
    assert lc.are_licenses_compatible('Unknown', unknownLic) == False
    assert lc.are_licenses_compatible('MIT', unknownLic) == False
    assert lc.are_licenses_compatible('MIT', 'Unknown') == False
    assert lc.are_licenses_compatible(unknownLic, 'Unknown') == False
    assert lc.are_licenses_compatible('Unknown', 'Unknown') == False
    assert lc.are_licenses_compatible(unknownLic, unknownLic) == False

