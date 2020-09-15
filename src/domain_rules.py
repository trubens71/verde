import src.utils as vutils
import src.draco_proxy as vdraco
import logging
import json
import networkx as nx
import os
from addict import Dict

CONTEXT = Dict()


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

    logging.info('building graph from properties in schema {}'.format(domain_schema_file_path))
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

    if CONTEXT.rule_config.rule_01_causal_relationships.export_graphml:
        graph_file = os.path.join(CONTEXT.directory, f'{CONTEXT.id}.graphml')
        logging.info(f'writing graph to {graph_file}')
        nx.write_graphml_xml(g, graph_file)
    elif export_file:
        nx.write_graphml_xml(g, export_file + '.graphml')

    return g


def test_x_y_preferences(g, test_cases=None):
    """
    Just a throwaway test function to try out the rule 01 graph
    :param g:
    :param test_cases:
    :return:
    """
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
            logging.fatal(f'node {node_pair[0]} not found')
            exit(1)

        if len(path) > 0:
            path_length[node_pair] = nx.dijkstra_path_length(g, node_pair[0], node_pair[1])
        else:
            path_length[node_pair] = float('inf')

        logging.debug(f'path length {path_length[node_pair]} from {node_pair[0]} to {node_pair[1]} by {path}')

    (x_var, y_var), min_len = min(path_length.items(), key=lambda x: x[1])

    if path_length[(x_var, y_var)] == path_length[(y_var, x_var)] != float('inf'):
        logging.info(f'found the same finite path length, so arbitrarily x={x_var}, y={y_var}')
    elif path_length[(x_var, y_var)] == path_length[(y_var, x_var)] == float('inf'):
        logging.info(f'found no paths in either direction, so arbitrarily x={x_var}, y={y_var}')
    else:
        logging.info(f'preference is x={x_var}, y={y_var} with path length {min_len}')

    if '.' in x_var:
        x_enc = x_var.split('.')[1]
    else:
        x_enc = None

    if '.' in y_var:
        y_enc = y_var.split('.')[1]
    else:
        y_enc = None

    return x_var, y_var, x_enc, y_enc


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


def bind_fields_to_encodings(fields):
    """
    Binds each field in query to an encoding in the base query.
    :param fields: dictionary of encodings and fields
    :return: a logic program of form: field(v_v,e0,"Displacement").
    """

    lp = ['\n% verde generated logic program','% binding fields to encodings']
    base_view = vdraco.get_default_view()
    for encoding_id in sorted(fields.keys()):
        lp.append(f'field({base_view},{encoding_id},"{fields[encoding_id]}").')
    return lp


def rule_01_causal_relationships(schema_file, mapping_json, query_enc_fields):

    global CONTEXT
    logging.info('applying verde rule 01 causal relationships')

    # Walk the domain schema to get nodes and edges
    dom_schema_nodes_edges = get_schema_nodes_and_edges(schema_file)

    # Each field from our input data may have one or more mappings into the schema
    enc_field_nodes = get_schema_nodes_for_source_fields(query_enc_fields, mapping_json)
    # This is a bit of a trick, but let the Dijkstra shortest_path algorithm take
    # care of the one-to-many field-to-node situation. i.e. get the shortest path from all entry points to the graph.
    field_nodes, field_schema_edges = get_encoding_fields_to_schema_edges(enc_field_nodes)
    # Build the graph
    dom_schema_graph = build_graph(*dom_schema_nodes_edges,
                                   field_nodes=field_nodes,
                                   field_edges=field_schema_edges)

    # Because we may have more than two fields in the query we need to consider all pairings that might get encoded
    # to the x and y channels, then get our preferences for each pair as we write the lp
    lp = ['\n% verde rule 1: x/y encoding preferences']
    enc_pairs = [(a, b) for a in enc_field_nodes.keys() for b in enc_field_nodes.keys() if a < b]
    for i, enc_pair in enumerate(enc_pairs):
        a = 'field.' + enc_pair[0] + '.' + enc_field_nodes[enc_pair[0]]['source_field']
        b = 'field.' + enc_pair[1] + '.' + enc_field_nodes[enc_pair[1]]['source_field']
        pref_x_var, pref_y_var, pref_x_enc, pref_y_enc = determine_x_y_preference(dom_schema_graph, (a, b))
        soft_weight = CONTEXT.rule_config.rule_01_causal_relationships.draco_soft_weight or 100
        lp.append(f'% for encoding pair {i} prefer x={pref_x_var} y={pref_y_var}')
        lp.append(f'soft(rule01_{pref_x_enc}_{pref_y_enc}) :- channel(V,{pref_y_enc},x), '
                  f'channel(V,{pref_x_enc},y), is_c_c(V).')
        lp.append(f'#const rule01_{pref_x_enc}_{pref_y_enc}_weight = {soft_weight}.')
        lp.append(f'soft_weight(rule01_{pref_x_enc}_{pref_y_enc},rule01_{pref_x_enc}_{pref_y_enc}_weight).')

    return lp


def create_verde_rules_lp(schema_file, mapping_file, query_enc_fields, trial_id, directory, rule_config, baseline_lp):

    logging.info(f'creating verde rules lp based on {schema_file} and {mapping_file}')

    global CONTEXT
    CONTEXT.id = trial_id
    CONTEXT.directory = directory
    CONTEXT.rule_config = rule_config

    # Fix the fields to the encodings so we can express rules in terms of encodings
    lp = bind_fields_to_encodings(query_enc_fields)

    # Load the input mapping json
    with open(mapping_file) as f:
        mapping_json = json.load(f)

    # Apply each verde rule to extend the lp
    if rule_config.rule_01_causal_relationships.do:
        lp = lp + rule_01_causal_relationships(schema_file, mapping_json, query_enc_fields)

    if rule_config.write_lp:
        lp_file = os.path.join(directory, f'{CONTEXT.id}_verde_rules_partial.lp')
        vutils.write_list_to_file(lp, lp_file, 'verde rules partial lp')
        lp_file = os.path.join(directory, f'{CONTEXT.id}_verde_schema_query.lp')
        vutils.write_list_to_file(baseline_lp + lp, lp_file, 'verde full schema and query lp')

    return baseline_lp + lp


if __name__ == "__main__":
    vutils.configure_logger('domain_rules.log', level=logging.DEBUG)
    nodes_edges = get_schema_nodes_and_edges('../schemas/verde_asc_domain_schema.json')
    graph = build_graph(*nodes_edges)
    test_x_y_preferences(graph)
    pass