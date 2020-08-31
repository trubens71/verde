import verde_old.verde_utils as vu
import logging
import json
import networkx as nx
import re
from collections import defaultdict


def get_schema_nodes_and_edges(domain_schema_file_path):
    """
    Takes a domain schema file path and builds a graph of connected domain terms.
    :param domain_schema_file_path:
    :return: networkx graph
    """

    nodes = []
    property_edges = []
    compose_edges = []
    explain_edges = []

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
                    pass  # We've looked ahead and seen this is a composition so don't want to create the edge or
                    # node yet. Yes it is ugly, but for definitions we want to expand fully which happens in the next
                    # recursion.
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
                elif v.split('/')[1] == 'properties':  # capture the composition of another property and walk no further
                    ref_path = '.'.join(v.split('/')[2:][::2])
                    edge = ('.'.join(prev_dom_path[0:-1]), ref_path)
                    logging.debug('COMPOSITION EDGE FROM {} TO {}'.format(edge[0], edge[1]))
                    compose_edges.append(edge)
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

    logging.info('Building graph from properties in schema {}'.format(domain_schema_file_path))
    walk(schema['properties'])

    logging.info(f'found {len(nodes)} nodes, {len(property_edges)} property edges, '
                 f'{len(compose_edges)} composition edges and {len(explain_edges)} explain edges')

    return nodes, property_edges, compose_edges, explain_edges


def build_graph(nodes, property_edges, compose_edges, explain_edges, field_nodes=None, field_edges=None,
                property_edge_weight=1, compose_edge_weight=0.5, explain_edge_weight=0.1, export_file=None):
    """
    Takes nodes and edges to build a directed, weighted graph. Standard edges have more weight than explain edges
    :param field_nodes:
    :param field_edges:
    :param nodes: a list of tuples of long node name and dict with short names. e.g. long=funder.budget, short=budget
    :param property_edges: list of tuples of long form nodes, for standard schema relationships
    :param compose_edges: per references to another property
    :param explain_edges: per property_edges but for explains cross-references between nodes.
    :param explain_edge_weight:
    :param compose_edge_weight:
    :param property_edge_weight:
    :param export_file:
    :return: a networkx graph
    """

    # The usual case is that we have edges from source fields to the schema nodes. The alt-case is for testing.
    # We treat them as properties, i.e. bidirectional with a weight of one.
    if field_nodes:
        nodes = nodes + field_nodes
    if field_edges:
        property_edges = property_edges + field_edges

    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from(property_edges, weight=property_edge_weight)
    # create reversed edges for property relationships
    property_edges_flip = list(map(lambda x: (x[1], x[0]), property_edges))
    g.add_edges_from(property_edges_flip, weight=property_edge_weight)
    g.add_edges_from(compose_edges, weight=compose_edge_weight)
    g.add_edges_from(explain_edges, weight=explain_edge_weight)

    if export_file:
        nx.write_graphml_xml(g, export_file + '.graphml')

    return g


def test_x_y_preferences(g, test_cases=None):
    if test_cases is None:
        test_cases = [
            ("funder.expenditure", "user.quality_of_life.well-being"),
            ("funder.expenditure", "user.demographics.age"),
            ("funder.org_unit.local_authority_name", "user.quality_of_life.well-being"),
            ("unpaid_carer", "user"),
            ("funder.budget", "service_provision"),
            ("funder", "user"),
            ("funder", "user.quality_of_life.well-being"),
            ("funder.expenditure", "user")
        ]

    for t, test_case in enumerate(test_cases):
        logging.info(f'===== Test Case {t + 1} =====')
        logging.info(f'Nodes are {test_case[0]} and {test_case[1]}')
        determine_x_y_preference(g, test_case)


def determine_x_y_preference(g, nodes):

    node_pairs = [nodes, (nodes[1], nodes[0])]
    path_length = {}

    for node_pair in node_pairs:
        path = []

        try:
            path = nx.dijkstra_path(g, node_pair[0], node_pair[1])
        except nx.NetworkXNoPath as np:
            path = []
        except nx.NodeNotFound as nnf:
            logging.fatal(f'Node {node_pair[0]} not found')
            exit(1)

        if len(path) > 0:
            path_length[node_pair] = nx.dijkstra_path_length(g, node_pair[0], node_pair[1])
        else:
            path_length[node_pair] = float('inf')

        logging.debug(f'path length {path_length[node_pair]} from {node_pair[0]} to {node_pair[1]} by {path}')

    (x_var, y_var), min_len = min(path_length.items(), key=lambda x: x[1])

    if path_length[(x_var, y_var)] == path_length[(y_var, x_var)] != float('inf'):
        logging.info(f'Found the same finite path length, so arbitrarily x={x_var}, y={y_var}')
    elif path_length[(x_var, y_var)] == path_length[(y_var, x_var)] == float('inf'):
        logging.info(f'Found no paths in either direction, so arbitrarily x={x_var}, y={y_var}')
    else:
        logging.info(f'Preference is x={x_var}, y={y_var} with path length {min_len}')

    return x_var, y_var


def get_schema_nodes_for_source_fields(encoding, mapping_json):

    def dotify_keys(d):
        # turn { "funder": { "expenditure": true } } into 'funder.expenditure'
        for k, v in d.items():
            if isinstance(v, dict):
                return k + '.' + dotify_keys(v)
            else:
                return k

    for enc in encoding.keys():
        encoding[enc]['schema_nodes'] = []
        for column in mapping_json:
            if column['column_name'] == encoding[enc]['source_field']:
                for mapping in column['domain_map']:
                    encoding[enc]['schema_nodes'].append(dotify_keys(mapping))
        logging.info(f"({enc},{encoding[enc]['source_field']}) is mapped to {encoding[enc]['schema_nodes']}")

    return encoding


def get_encoding_fields_to_schema_edges(encodings):
    # enc is a dictionary of encodings containing lists of schema_nodes.
    # Create edges between each encoding field and its mapped schema node.

    nodes = []
    all_edges = []

    for enc in encodings.keys():
        field = encodings[enc]['source_field']
        schema_nodes = encodings[enc]['schema_nodes']
        field_node = 'field.' + enc + '.' + field  # a bit verbose but should avoid conflict with schema node names
        nodes.append((field_node, {'short': field_node}))
        edges = list(zip([field_node]*len(schema_nodes), schema_nodes))
        logging.debug(f'Adding field nodes to graph with edges {edges}')
        all_edges = all_edges + edges

    return nodes, all_edges


def create_verde_rule_asp(query_asp, domain_schema_file_path, input_mapping_file_path, graph_file=None):
    logging.info(f'Creating verde_old rules based on {domain_schema_file_path} and {input_mapping_file_path}')

    # Load the input mapping json
    with open(input_mapping_file_path) as f:
        mapping_json = json.load(f)
    mapping_json = vu.fix_json_column_name(mapping_json)  # get rid of special chars in column names

    # Walk the domain schema to get nodes and edges
    dom_schema_nodes_edges = get_schema_nodes_and_edges(domain_schema_file_path)

    # Find the encoding fields in the query asp
    encodings = defaultdict(dict)
    r = re.compile(r'field\((.*),\"(.*)\"\).')  # e.g. field(e0,"Social_care_related_quality_of_life_score_All").
    for field_fact in list(filter(r.search, query_asp)):
        logging.debug(f'Found field: {field_fact}')
        m = re.search(r, field_fact)
        encodings[m.group(1)]['source_field'] = m.group(2)  # tuple of encoding id and field name

    # Each field from our input data may have one or more mappings into the schema
    encodings = get_schema_nodes_for_source_fields(encodings, mapping_json)
    # Add fields to the domain graph. This is a bit of a trick, but let's the Dijkstra shortest_path algorithm to take
    # care of the one-to-many field-to-node situation. i.e. get the shortest path from all entry points to the graph.
    field_nodes, field_schema_edges = get_encoding_fields_to_schema_edges(encodings)
    dom_schema_graph = build_graph(*dom_schema_nodes_edges,
                                   field_nodes = field_nodes,
                                   field_edges=field_schema_edges)

    if graph_file:
        nx.write_graphml_xml(dom_schema_graph, graph_file + '.graphml')

    # Because we may have more than two fields in the query we need to consider all pairings that might get encoded
    # to the x and y channels, then get our preferences for each pair as we write the asp
    asp = ['% Verde rule 1: x/y encoding preferences']
    enc_pairs = [(a, b) for a in encodings.keys() for b in encodings.keys() if a < b]
    for i, enc_pair in enumerate(enc_pairs):
        a = 'field.' + enc_pair[0] + '.' + encodings[enc_pair[0]]['source_field']
        b = 'field.' + enc_pair[1] + '.' + encodings[enc_pair[1]]['source_field']
        pref_x_var, pref_y_var = determine_x_y_preference(dom_schema_graph, (a,b))
        asp.append(f'% for encoding pair {i} prefer x={pref_x_var} y={pref_y_var}')
        ea, eb = enc_pair
        asp.append(f'soft({ea}_{eb}) :- channel({ea},x), not channel({ea},y), channel({eb},y), not channel({eb},x).')
        asp.append(f'#const {ea}_{eb}_weight = 1.')
        asp.append(f'soft_weight({ea}_{eb},{ea}_{eb}_weight).')

    for line in asp:
        logging.debug(line)

    return asp


if __name__ == "__main__":
    vu.configure_logger('rule_gen.log', level=logging.DEBUG)
    nodes_edges = get_schema_nodes_and_edges('../schemas/verde_asc_domain_schema.json')
    graph = build_graph(*nodes_edges, export_file='schema_prop_multi_compose_explain')
    test_x_y_preferences(graph)
    pass
