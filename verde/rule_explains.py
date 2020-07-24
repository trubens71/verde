import verde.verde_utils as vu
import logging
import json
import networkx as nx
import matplotlib.pyplot as plt


def get_schema_nodes_and_edges(domain_schema_file_path):
    """
    Takes a domain schema file path and builds a graph of connected domain terms.
    :param domain_schema_file_path:
    :return: networkx graph

    TODO: Rename and move this function. It's for more than the explains rule. We are walking the schema so need to
     build up data structure to support each rule type, not just the graph for the explains rule.
    """

    nodes = []
    property_edges = []
    jump_edges = []
    explain_edges = []

    def walk_old(d, path=None, dom_path=None):
        """
        Take a dict and recursively walk it, collecting domain specific terms and building a graph between them.
        Is able to instantiate $ref cross-references.
        :param d: dictionary to walk
        :param path: list of nodes in the current recursion stack
        :param dom_path: list of domain specific terms in the current recursion stack.
        :return: nothing
        """

        if path is None:  # full technical path
            path = ['properties']
        if dom_path is None:  # domain specific terms only, no json schema reserved words
            dom_path = []

        for k, v in d.items():
            path.append(k)
            prev_dom_path = dom_path.copy()

            # Extend the domain path and the network
            if path[-2] == 'properties':  # all domain specific terms will be properties
                dom_path.append(k)
                nodes.append(('.'.join(dom_path), {"short": k}))

            # Handle case of $refs between nodes across the schema
            if k == '$ref':  # dig into the original schema to instantiate the reference
                if v.split('/')[1] == 'definitions':
                    # expand the ref to definitions
                    nonlocal schema
                    schema_part = schema
                    for node in v.split('/')[1:]:  # ignore leading '#' and walk down schema to the node referenced
                        schema_part = schema_part[node]
                    v = schema_part
                elif v.split('/')[1] == 'properties':
                    # capture the jump to another property but walk no further
                    ref_path = '.'.join(v.split('/')[2:][::2])
                    edge = ('.'.join((prev_dom_path)[0:-1]), ref_path)
                    logging.debug('JUMP EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                    jump_edges.append(edge)
                    v = None  # walk no further, this is just a cross-reference we don't need to expand

            # Deal with our rule directives
            if k == 'verde_rule_directive':
                for vrd_k, vrd_v in v.items():
                    if vrd_k == "explains":
                        v = vrd_v
                    elif vrd_k == 'ordinal':
                        logging.debug('ORDINAL RULE VALUES FOR {} ARE {}'.format(nodes[-1][0], vrd_v))
                        nodes[-1][1]['ordinal'] = ','.join(vrd_v)
                    else:
                        logging.warning('ignored verde_rule_directive {} with values {}'.format(vrd_k, vrd_v))

            # Handle a leaf which is a verde explains rule reference
            if path[-2] == 'verde_rule_directive' and path[-1] == '$ref':
                # We want the domain path from the referenced path.
                # That's every other element after json preamble.
                # e.g. '#/properties/user/properties/quality_of_life' -> ['user','quality_of_life']
                ref_path = '.'.join(d['$ref'].split('/')[2:][::2])
                edge = ('.'.join(prev_dom_path), ref_path)
                logging.debug('EXPLAINS EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                explain_edges.append(edge)
                v = None  # walk no further, this is just a cross-reference we don't need to expand

            if len(prev_dom_path) > 0 and path[-2] == 'properties':  # don't create edge for first node processed
                edge = ('.'.join(prev_dom_path), '.'.join(dom_path))
                logging.debug('PROPERTY EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                property_edges.append(edge)

            # Recurse over remainder of schema
            if isinstance(v, dict):
                walk(v, path, dom_path)
            elif isinstance(v, list):
                for v_item in v:
                    if isinstance(v_item, dict):
                        walk(v_item, path, dom_path)

            # symmetry with appends above to walk back up by one node before next loop
            if path[-2] == 'properties':
                dom_path.pop()
            path.pop()

    def walk(d, path=None, dom_path=None):

        if path is None:  # full technical path
            path = ['properties']
        if dom_path is None:  # domain specific terms only, no json schema reserved words
            dom_path = []

        for k, v in d.items():
            path.append(k)
            prev_dom_path = dom_path.copy()

            if path[-2] == 'properties':  # all domain specific terms will be properties
                dom_path.append(k)

            logging.debug(f"PATH {'.'.join(path)}")
            logging.debug(f"\t PREV_DOM_PATH {'.'.join(prev_dom_path)}")
            logging.debug(f"\t CURR_DOM_PATH {'.'.join(dom_path)}")

            # Recurse over remainder of schema
            if isinstance(v, dict):
                walk(v, path, dom_path)
            elif isinstance(v, list):
                for v_item in v:
                    if isinstance(v_item, dict):
                        walk(v_item, path, dom_path)

            # symmetry with appends above to walk back up by one node before next loop
            path.pop()

    with open(domain_schema_file_path, 'r') as f:
        schema = json.load(f)

    logging.info('Processing properties in schema {}'.format(domain_schema_file_path))
    walk(schema['properties'])

    logging.info(f'found {len(nodes)} nodes, {len(property_edges)} property edges, '
                 f'{len(jump_edges)} jump edges and {len(explain_edges)} explain edges')

    return nodes, property_edges, jump_edges, explain_edges


def build_graph(nodes, std_edges, explain_edges, std_edge_weight=1, explain_edge_weight=0.1, export_file=None):
    """
    Takes nodes and edges to build a directed, weighted graph. Standard edges have more weight than explain edges
    :param nodes: a list of tuples of long node name and dict with short names. e.g. long=funder.budget, short=budget
    :param std_edges: list of tuples of long form nodes, for standard schema relationships
    :param explain_edges: per std_edges but for explains cross-references between nodes.
    :return: a networkx graph
    """
    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from(std_edges, weight=std_edge_weight)
    g.add_edges_from(explain_edges, weight=explain_edge_weight)

    if export_file:
        nx.write_graphml_xml(g, export_file + '.graphml')

    return g


def create_asp_for_explains(domain_schema_file_path, input_mapping_file_path, schema_asp):
    pass


if __name__ == "__main__":
    vu.configure_logger('rule_explains.log', level=logging.DEBUG)
    nodes_edges = get_schema_nodes_and_edges('../schemas/verde_asc_domain_schema.json')
#    graph = build_graph(*nodes_edges, export_file='schema_v2')
    pass
