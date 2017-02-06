from . import analyze
from .bom import Bom, SourcePosition

def test_collect_license_warnings():
    def license_warnings(data, is_source_dist=False):
        return analyze.collect_license_warnings(Bom(data, '.'), is_source_dist)

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

def test_analyze_bom():
    data = {
        'license': 'AllRightsReserved',
        'dependencies': [{'root': 'foss', 'license': 'GPL-3.0'}]
    }
    assert analyze.analyze_bom(Bom(data, '.')) == ["The license 'AllRightsReserved' may be incompatible with the license 'GPL-3.0' in 'foss'. Specify 'copyright-holders' and/or 'licensees' to state the license is authorized in this context. If this dependency is used only for development, move it to the 'development-dependencies' section."]

