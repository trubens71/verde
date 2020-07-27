import verde.verde_utils as vu
import logging
import json
import networkx as nx


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
        nonlocal schema  # we will need to expand $refs to definitions hence access to entire schema

        for k, v in d.items():
            path.append(k)
            prev_dom_path = dom_path.copy()

            if path[-2] == 'properties':  # all domain specific nodes will be properties
                dom_path.append(k)
                if isinstance(v, dict) and '$ref' in v.keys() and v['$ref'].split('/')[1] == 'properties':
                    pass  # We've looked ahead and seen this is a jump so don't want to create the edge or node yet.
                    # Yes it is ugly, but for definitions we want to expand fully which happens in next recursion.
                else:
                    logging.debug(f"ADDING NODE {'.'.join(dom_path)}")
                    nodes.append(('.'.join(dom_path), {"short": k}))
                    if len(prev_dom_path) > 0:  # only create edge if we have a parent
                        edge = ('.'.join(prev_dom_path), '.'.join(dom_path))
                        logging.debug('PROPERTY EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                        property_edges.append(edge)

            if k == '$ref' and path[-3] == 'properties':  # normal schema cross-reference
                if v.split('/')[1] == 'definitions':  # expand the ref to definitions
                    schema_part = schema
                    for node in v.split('/')[1:]:  # ignore leading '#' and walk down schema to the node referenced
                        schema_part = schema_part[node]
                    v = schema_part  # expansion has occurred now, so the definition will get walked
                elif v.split('/')[1] == 'properties':  # capture the jump to another property and walk no further
                    ref_path = '.'.join(v.split('/')[2:][::2])
                    edge = ('.'.join(prev_dom_path[0:-1]), ref_path)
                    logging.debug('JUMP EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                    jump_edges.append(edge)
                    v = None

            if k == '$ref' and path[-3:-1] == ['verde_rule_directive', 'explains']:  # explain and walk no further
                ref_path = '.'.join(v.split('/')[2:][::2])
                edge = ('.'.join(prev_dom_path), ref_path)
                logging.debug('EXPLAINS EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                explain_edges.append(edge)
                v = None

            # Deal with our rule directives
            if k == 'verde_rule_directive':
                for vrd_k, vrd_v in v.items():
                    if vrd_k == "explains":
                        v = vrd_v
                        path.append(vrd_k)
                    elif vrd_k == 'ordinal':
                        logging.debug('ORDINAL RULE VALUES FOR {} ARE {}'.format(nodes[-1][0], vrd_v))
                        nodes[-1][1]['ordinal'] = ','.join(vrd_v)
                    else:
                        logging.warning('ignored verde_rule_directive {} with values {}'.format(vrd_k, vrd_v))

            # Recurse over remainder of schema
            if isinstance(v, dict):
                walk(v, path, dom_path)
            elif isinstance(v, list):
                for v_item in v:
                    if isinstance(v_item, dict):
                        walk(v_item, path, dom_path)

            # symmetry with the appends above to walk back up by one node before next loop
            if k == 'verde_rule_directive' and path[-1] == 'explains':
                path.pop()
            if path[-2] == 'properties':
                dom_path.pop()
            path.pop()

    with open(domain_schema_file_path, 'r') as f:
        schema = json.load(f)

    logging.info('Processing properties in schema {}'.format(domain_schema_file_path))
    walk(schema['properties'])

    logging.info(f'found {len(nodes)} nodes, {len(property_edges)} property edges, '
                 f'{len(jump_edges)} jump edges and {len(explain_edges)} explain edges')

    return nodes, property_edges, jump_edges, explain_edges


def build_graph(nodes, property_edges, jump_edges, explain_edges,
                property_edge_weight=1, jump_edge_weight=0.5, explain_edge_weight=0.1, export_file=None):
    """
    Takes nodes and edges to build a directed, weighted graph. Standard edges have more weight than explain edges
    :param nodes: a list of tuples of long node name and dict with short names. e.g. long=funder.budget, short=budget
    :param property_edges: list of tuples of long form nodes, for standard schema relationships
    :param jump_edges: per references to another property
    :param explain_edges: per property_edges but for explains cross-references between nodes.
    :param explain_edge_weight:
    :param jump_edge_weight:
    :param property_edge_weight:
    :param export_file:
    :return: a networkx graph
    """

    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from(property_edges, weight=property_edge_weight)
    # create parallel reversed edges for property relationships
    property_edges_flip = list(map(lambda x: (x[1], x[0]), property_edges))
    g.add_edges_from(property_edges_flip, weight=property_edge_weight)
    g.add_edges_from(jump_edges, weight=jump_edge_weight)
    g.add_edges_from(explain_edges, weight=explain_edge_weight)

    if export_file:
        nx.write_graphml_xml(g, export_file + '.graphml')

    return g


def test_paths_in_graph(g, test_cases=None):

    if test_cases is None:
        test_cases = [
            ("funder.expenditure", "user.quality_of_life.well-being"),
            ("funder.expenditure", "user.demographics.age"),
            ("funder.org_unit.local_authority_name", "user.quality_of_life.well-being"),
            ("unpaid_carer", "user"),
            ("funder.budget", "service_provision"),
            ("funder", "user")
        ]

    for t, test_case in enumerate(test_cases):
        logging.info(f'===== Test Case {t+1} =====')
        logging.info(f'Nodes are {test_case[0]} and {test_case[1]}')

        node_pairs = [test_case, (test_case[1], test_case[0])]
        path_length = {}

        for node_pair in node_pairs:
            path = []

            try:
                path = nx.dijkstra_path(g,node_pair[0], node_pair[1])
            except nx.NetworkXNoPath as np:
                path = []
            except nx.NodeNotFound as nnf:
                logging.fatal(f'Node {node_pair[0]} not found')
                exit(1)

            if len(path) > 0:
                path_length[node_pair] = nx.dijkstra_path_length(g, node_pair[0], node_pair[1])
            else:
                path_length[node_pair] = float('inf')

            logging.info(f'path length {path_length[node_pair]} from {node_pair[0]} to {node_pair[1]} by {path}')

        shortest = min(path_length.items(), key=lambda x: x[1])
        x_var, y_var = shortest[0]

        if path_length[(x_var, y_var)] == path_length[(y_var, x_var)] != float('inf'):
            logging.info(f'verde found the same finite path length, so arbitrarily x={x_var}, y={y_var}')
        elif path_length[(x_var, y_var)] == path_length[(y_var, x_var)] == float('inf'):
            logging.info(f'verde found no paths in either direction, so arbitrarily x={x_var}, y={y_var}')
        else:
            logging.info(f'verde prefers x={x_var}, y={y_var}')


def create_asp_for_explains(domain_schema_file_path, input_mapping_file_path, schema_asp):
    pass


if __name__ == "__main__":
    vu.configure_logger('rule_explains.log', level=logging.DEBUG)
    nodes_edges = get_schema_nodes_and_edges('../schemas/verde_asc_domain_schema.json')
#    graph = build_graph(*nodes_edges, export_file='schema_3edgetypes')
    graph = build_graph(*nodes_edges, export_file='schema_prop_multi_jump_explain')
    test_paths_in_graph(graph)
    pass

