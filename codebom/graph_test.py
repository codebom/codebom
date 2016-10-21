from . import graph
from .bom import Bom

class MockDigraph(object):
    def __init__(self):
        self._nodes = []
        self._edges = []

    def __repr__(self):
        return 'MockDigraph(_nodes={}, _edges={})'.format(self._nodes, self._edges)

    def node(self, *args, **kwargs):
        self._nodes.append(kwargs)

    def edge(self, *args, **kwargs):
        self._edges.append(kwargs)

def make_graph(data, **kwargs):
    dot = MockDigraph()
    graph._add_node(dot, Bom(data, '.'), False, **kwargs)
    return dot

def is_compatible(data, **kwargs):
    """
    Return False if the top node is marked red, indicating a license conflict
    exists in a distributed dependency.
    """
    return make_graph(data, **kwargs)._edges[0].get('color') == None

def test_add_node():
    assert is_compatible({'dependencies': [{}]}) is False
    assert is_compatible({'development-dependencies': [{}]}) is True

    assert is_compatible({'development-dependencies': [{}]}, is_source_dist=True) is False
    assert is_compatible({'dependencies': [{'dependencies': [{}]}]}) is False
    assert is_compatible({'development-dependencies': [{'dependencies': [{}]}]}, is_source_dist=True) is False

def test_graph_bom():
    assert graph.graph_bom(Bom({}, '.')).source
