import src.utils as vutils
import logging
import json
import networkx as nx
import os
from addict import Dict
import itertools

CONTEXT = Dict()

# TODO per github issue #7, consider whether we should write rules for all fields, not just the query fields.
#      Will be slower but might be important if we can get draco to start introducing further fields


def get_schema_nodes_and_edges(domain_schema_file_path, for_rule='rule01'):
    """
    Takes a domain schema file path and builds a graph of connected domain terms.
    :param for_rule: for rule03 only return the ordinals.
    :param domain_schema_file_path:
    :return: networkx graph
    """

    nodes = []
    property_edges = []
    compose_edges = []
    explain_edges = []
    domain_node_ordinals = {}

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
                        domain_node_ordinals['.'.join(dom_path)] = vrd_v
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

    if for_rule == 'rule03':
        return domain_node_ordinals
    else:
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
    # TODO deprecated, remove when rule_01v02_causal_relationships and determine_explanatory_response_preference
    #      are proven
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


def determine_explanatory_response_preference(g, nodes):

    """
    Take a graph and two nodes. Attempt to determine which node might be explanatory and which
    might be a response variable based on the path lengths between the nodes.
    :param g:
    :param nodes:
    :return:
    """
    prefix = 'field.'  # we use this in the graph to avoid confusion with domain model nodes
    nodes = (f'{prefix}{nodes[0]}', f'{prefix}{nodes[1]}')

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

    (expl_var, resp_var), min_len = min(path_length.items(), key=lambda x: x[1])

    if path_length[(expl_var, resp_var)] == path_length[(resp_var, expl_var)] != float('inf'):
        logging.info(f'found the same finite path length, so arbitrarily explanatory={expl_var}, response={resp_var}')
    elif path_length[(expl_var, resp_var)] == path_length[(resp_var, expl_var)] == float('inf'):
        logging.info(f'found no paths in either direction, so arbitrarily explanatory={expl_var}, response={resp_var}')
    else:
        logging.info(f'preference is explanatory={expl_var}, response={resp_var} with path length {min_len}')

    # take off the prefix
    expl_var = expl_var[len(prefix):] if expl_var.startswith(prefix) else expl_var
    resp_var = resp_var[len(prefix):] if resp_var.startswith(prefix) else resp_var

    return expl_var, resp_var


def get_schema_nodes_for_source_fields(query_fields, mapping_json):
    """
    For a list of fields (from the query) determine the mapped schema nodes
    :param query_fields:
    :param mapping_json:
    :return:
    """
    def dotify_keys(d):
        # turn { "funder": { "expenditure": true } } into 'funder.expenditure'
        for k, v in d.items():
            if isinstance(v, dict):
                if len(v):
                    return k + '.' + dotify_keys(v)
                else:
                    return k  # this is the case where we map to a non-leaf node in the domain model
            else:
                return k

    field_nodes = Dict()

    for field in query_fields:
        field_nodes[field]['schema_nodes'] = []
        for column in mapping_json:
            if column['column_name'] == field:
                for mapping in column['domain_map']:
                    field_nodes[field]['schema_nodes'].append(dotify_keys(mapping))
        logging.info(f"{field} is mapped to {field_nodes[field]['schema_nodes']}")

    return field_nodes


def get_field_nodes_and_edges_to_schema(field_nodes):
    """
     enc is a dictionary of fields with lists of schema_nodes.
    Create edges between each field and its mapped schema nodes.
    :param field_nodes:
    :return:
    """

    nodes = []
    all_edges = []

    for field in field_nodes.keys():
        schema_nodes = field_nodes[field]['schema_nodes']
        field_node = f'field.{field}'  # a bit verbose but should avoid conflict with schema node names
        nodes.append((field_node, {'short': field_node}))
        edges = list(zip([field_node]*len(schema_nodes), schema_nodes))
        logging.debug(f'Adding field nodes to graph with edges {edges}')
        all_edges = all_edges + edges

    return nodes, all_edges


def rule_01_causal_relationships(context, schema_file, mapping_json, query_fields):

    # sort this out higher up, later!
    # query_fields = [query_enc_fields[enc]['source_field'] for enc in query_enc_fields.keys()]

    global CONTEXT
    CONTEXT = context
    logging.info('applying verde rule 01v03 (causal relationships)')

    # Walk the domain schema to get nodes and edges
    dom_schema_nodes_edges = get_schema_nodes_and_edges(schema_file)

    # Each field from our input data may have one or more mappings into the schema
    field_to_nodes = get_schema_nodes_for_source_fields(query_fields, mapping_json)
    # This is a bit of a trick, but let the Dijkstra shortest_path algorithm take
    # care of the one-to-many field-to-node situation. i.e. get the shortest path from all entry points to the graph.
    field_nodes, field_schema_edges = get_field_nodes_and_edges_to_schema(field_to_nodes)
    # Build the graph
    rule_config = CONTEXT.rule_config.rule_01v02_causal_relationships
    property_edge_weight = rule_config.property_edge_weight if rule_config.property_edge_weight else 1.0
    compose_edge_weight = rule_config.compose_edge_weight if rule_config.compose_edge_weight else 0.5
    explain_edge_weight = rule_config.explain_edge_weight if rule_config.explain_edge_weight else 0.1

    dom_schema_graph = build_graph(*dom_schema_nodes_edges,
                                   field_nodes=field_nodes,
                                   field_edges=field_schema_edges,
                                   property_edge_weight=property_edge_weight,
                                   compose_edge_weight=compose_edge_weight,
                                   explain_edge_weight=explain_edge_weight)

    # Because we may have more than two fields in the query we need to consider all pairings that might get encoded
    # to the channels, then get our preferences for each pair as we write the lp
    lp = ['\n% verde rule 01v03: x/y/size/colour encoding preferences based on possible causal relationships']
    field_pairs = list(itertools.combinations(field_to_nodes.keys(), 2))
    channels = ['x', 'y', 'size', 'color']  # order of this list is important
    # itertools.combinations is deterministic according to docs, so pairs will be ordered as they appear in the list
    channel_pairs = list(itertools.combinations(channels, 2))
    soft_weight = CONTEXT.rule_config.rule_01v02_causal_relationships.draco_soft_weight or 100

    for i, field_pair in enumerate(field_pairs):

        # get preference for explanatory versus response variables for the two fields
        expl_var, resp_var = determine_explanatory_response_preference(dom_schema_graph, field_pair)

        for j, channel_pair in enumerate(channel_pairs):

            expl_channel, resp_channel = channel_pair  # based on channel list order and deterministic itertools.
            rule = f'rule01v03_{i:02}_{j:02}'

            # create a soft rule which assigns a cost to not observing our preference for encoding/channel mappings
            lp.append(f'% for encoding pair {i} / channel pair {j} we prefer '
                      f'{expl_channel}={expl_var} {resp_channel}={resp_var}')

            lp.append(f'soft({rule},V) :- channel(V,E1,{expl_channel}), '
                      f'field(V,E1,\"{resp_var}\"), '
                      f'channel(V,E2,{resp_channel}), '
                      f'field(V,E2,\"{expl_var}\"), '
                      f' is_c_c(V).')

            lp.append(f'#const {rule}_weight = {soft_weight}.')
            lp.append(f'soft_weight({rule},{rule}_weight).')

    return lp


if __name__ == "__main__":
    vutils.configure_logger('domain_rules.log', level=logging.DEBUG)
    nodes_edges = get_schema_nodes_and_edges('../schemas/verde_asc_domain_schema.json')
    graph = build_graph(*nodes_edges)
    test_x_y_preferences(graph)
    pass
