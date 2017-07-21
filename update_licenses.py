#!/usr/bin/env python

import rdflib
from collections import OrderedDict
from pprint import pprint
import os
import sys

empty_header = "There is no standard license header for the license"

def get_license_ids():
    graph = rdflib.Graph()
    graph.parse('http://spdx.org/licenses/index.html', 'rdfa')
    ref = rdflib.URIRef('http://spdx.org/rdf/terms#licenseId')
    objs = graph.subject_objects(ref)
    return map(lambda x: x[1].value, objs)

def lit_to_str(lit):
    s = lit.nodeValue if lit.nodeValue else ''
        
    return s + xml_to_str(lit)

def xml_to_str(parent):
    return ''.join(lit_to_str(x) for x in parent.childNodes)

def license_text_to_str(literal):
    # Python 3 expect a str object
    if isinstance(literal.value, str):
        return literal.value

    # Assume the literal contains a list of <p> elements under a top level node.
    return xml_to_str(literal.value.firstChild) + '\n'

def get_license_text(license_id):
    return get_license_term(license_id, "http://spdx.org/rdf/terms#licenseText")

def get_license_header(license_id):
    return get_license_term(license_id, "http://spdx.org/rdf/terms#standardLicenseHeader")

def get_license_term(license_id, term):
    graph = rdflib.Graph()

    try:
        graph.parse('http://spdx.org/licenses/' + license_id + '.html')
    except:
        return None

    ref = rdflib.URIRef(term)
    objs = graph.subject_objects(ref)
    return license_text_to_str(next(objs)[1])

def write_licenses_dir(ids):
    license_dir = 'codebom/licenses'
    if not os.path.exists(license_dir):
        os.makedirs(license_dir)

    for license_id in ids:
        sys.stdout.write("Updating license text for '{}'\n".format(license_id))
        text = get_license_text(license_id)
        if text is None:
            continue
        
        write_license_text(license_dir, license_id, text)
        
        header = get_license_header(license_id)
        if header is not None and header.strip() != empty_header:
            write_license_header(license_dir, license_id, header)

def write_license_text(license_dir, license_id, text):
    write_content(license_dir, license_id, "", text)

def write_license_header(license_dir, license_id, header):
    write_content(license_dir, license_id, "-header", header)

def write_content(license_dir, license_id, suffix, text):
        with open('{}/{}{}.txt'.format(license_dir, license_id, suffix), 'w') as hdl:
            hdl.write(text)

with open('codebom/licenses.py', 'w') as out:
    ids = list(get_license_ids())
    ids.sort()
    out.write('license_ids = ')
    pprint(ids, indent=4, stream=out)

    write_licenses_dir(ids)
