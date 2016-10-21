import argparse
from . import _version
import sys
import os.path
import io

def get_default_bom():
    if sys.stdin.isatty():
        name = '.bom.yaml'
        return os.path.isfile(name) and name or None
    else:
        return sys.stdin

def parse_args(argv):
    """
    Return a dictionary with the parsed arguments from 'argv'.
    """
    parser = argparse.ArgumentParser(description='Validate a Bill of Materials')
    parser.add_argument('--version', action='version', version=_version.__version__)

    parser.add_argument('-f', metavar='FILE', default=get_default_bom(), type=argparse.FileType())

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    scan_parser = subparsers.add_parser('scan', help='Scan for missing declarations')
    scan_parser.add_argument('--source-distribution', action='store_true')
    scan_parser.add_argument('--recursive', '-r', action='store_true', help='Recurse into components')
    scan_parser.add_argument('--add', '-a', action='store_true', help='Add missing declarations to output')
    scan_parser.add_argument('--coalesce', default='all', choices=['all', 'none'], help='Merge declarations')
    scan_parser.add_argument('-o', metavar='FILE', default=sys.stdout, type=argparse.FileType('w'))

    verify_parser = subparsers.add_parser('verify', help='Verify declarations are consistent')
    verify_parser.add_argument('--source-distribution', action='store_true')
    verify_parser.add_argument('-o', metavar='FILE', default=sys.stdout, type=argparse.FileType('w'))
    verify_parser.add_argument('--check-origins', choices=['uri', 'contents'])

    graph_parser = subparsers.add_parser('graph', help='Graph license dependencies')
    graph_parser.add_argument('--source-distribution', action='store_true')
    graph_parser.add_argument('-o', metavar='FILE', default=sys.stdout, type=argparse.FileType('wb'))

    return parser.parse_args(argv)
