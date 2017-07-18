#!/usr/bin/env python

import rdflib
from collections import OrderedDict
from pprint import pprint
import os
import sys

def get_license_ids():
    graph = rdflib.Graph()
    graph.parse('http://spdx.org/licenses/index.html', 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)

def lit_to_str(lit):
    s = lit.nodeValue.encode('utf-8') if lit.nodeValue else ''
    return s + xml_to_str(lit)

def xml_to_str(parent):
    return ''.join(lit_to_str(x) for x in parent.childNodes)

def license_text_to_str(literal):
    if isinstance(literal.value, unicode):
        return literal.value.encode('utf-8')

    # Assume the literal contains a list of <p> elements under a top level node.
    return xml_to_str(literal.value.firstChild) + '\n'

def get_license_text(licenseId):
    return get_license_term(licenseId, "http://spdx.org/rdf/terms#licenseText")

def get_license_header(licenseId):
    return get_license_term(licenseId, "http://spdx.org/rdf/terms#standardLicenseHeader")

def get_license_term(licenseId, term):
    graph = rdflib.Graph()

    try:
        graph.parse('http://spdx.org/licenses/' + licenseId + '.html')
    except:
        return None

    ref = rdflib.URIRef(term)
    objs = graph.subject_objects(ref)
    return license_text_to_str(objs.next()[1])

def write_licenses_dir(ids):
    licenseDir = 'codebom/licenses'
    if not os.path.exists(licenseDir):
        os.makedirs(licenseDir)

    for licenseId in ids:
        sys.stdout.write("Updating license text for '{}'\n".format(licenseId))
        text = get_license_text(licenseId)
        if text is None:
            continue
        
        write_license_text(licenseDir, licenseId, text)
        
        header = get_license_header(licenseId)
        if header is not None:
            write_license_header(licenseDir, licenseId, header)

def write_license_text(licenseDir, licenseId, text):
    write_content(licenseDir, licenseId, "", text)

def write_license_header(licenseDir, licenseId, header):
    write_content(licenseDir, licenseId, "-header", header)

def write_content(licenseDir, licenseId, suffix, text):
        with open('{}/{}{}.txt'.format(licenseDir, licenseId, suffix), 'w') as hdl:
            hdl.write(text)

with open('codebom/licenses.py', 'w') as out:
    ids = get_license_ids()
    ids.sort()
    out.write('license_ids = ')
    pprint(ids, indent=4, stream=out)

    write_licenses_dir(ids)
