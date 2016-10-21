from graphviz import Digraph
from .licenseconflict import is_dependent_license_compatible

def _add_edge(dot, parent_id, node_id, is_tainted, is_development):
    attrs = {}
    if is_development:
        attrs['style'] = 'dashed'
    elif is_tainted:
        attrs['color'] = 'red'

    dot.edge(parent_id, node_id, **attrs)

_last_node_id = 0

def _add_node(dot, bom, is_dev, **kwargs):
    is_source_dist = kwargs.get('is_source_dist')
    is_tainted = False

    deps = {}
    for x in bom.dependencies:
        k, dep_tainted = _add_node(dot, x, is_dev, **kwargs)
        if dep_tainted and not is_dev:
            is_tainted = True
        deps[k] = (x, dep_tainted)

    dev_deps = {}
    for x in bom.development_dependencies:
        k, dep_tainted = _add_node(dot, x, is_dev or not is_source_dist, **kwargs)
        if dep_tainted and is_source_dist:
            is_tainted = True
        dev_deps[k] = (x, dep_tainted)

    global _last_node_id
    node_id = 'A{}'.format(_last_node_id)
    _last_node_id += 1

    all_deps = is_source_dist and bom.all_dependencies or bom.dependencies
    is_tainted = is_tainted or any(not is_dependent_license_compatible(bom, x) for x in all_deps)
    attrs = {}
    if is_tainted and not is_dev:
        attrs['style'] = 'filled'
        attrs['fillcolor'] = 'pink'
    dot.node(node_id, bom.name, **attrs)

    for k, (dep, dep_tainted) in deps.items():
        tainted = not is_dev and (dep_tainted or not is_dependent_license_compatible(bom, dep))
        _add_edge(dot, node_id, k, tainted, False)

    for k, (dep, dep_tainted) in dev_deps.items():
        tainted = not is_dev and (dep_tainted or not is_dependent_license_compatible(bom, dep))
        _add_edge(dot, node_id, k, tainted, not is_source_dist)

    return (node_id, is_tainted)

def graph_bom(bom, **kwargs):
    """
    Return a Digraph for the given 'bom'
    """
    dot = Digraph(comment='License dependency diagram')
    _add_node(dot, bom, False, **kwargs)

    return dot
