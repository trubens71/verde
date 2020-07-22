import verde.verde_utils as vu
import logging
import json


def build_domain_graph(domain_schema_file_path):
    """
    Takes a domain schema file path and builds a graph of connected domain terms.
    :param domain_schema_file_path:
    :return: networkx graph

    //TODO Rename and move this function. It's for more than the explains rule.
    //TODO We are walking the schema so need to build up data structure to support each rule type, not just the
    //TODO graph for the explains rule.
    """

    def walk(d, path=None, dom_path=None):
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

            # Handle special cases
            if k == '$ref':  # dig into the original schema to instantiate the reference
                nonlocal schema
                schema_part = schema
                for node in v.split('/')[1:]:  # ignore leading '#' and walk down schema to the node referenced
                    schema_part = schema_part[node]
                v = schema_part

            if k == 'verde_rule_directive': # schema currently has "_$ref" to effectively comment the explains out
                for vrd_k, vrd_v in v.items():
                    if vrd_k == "explains":
                        v = vrd_v
                    else:
                        logging.warning('verde_rule_directive {} ignored with values {}'.format(vrd_k, vrd_v))

            # Extend the domain path and the network
            if path[-2] == 'properties':  # all domain specific terms will be properties
                dom_path.append(k)

            # Handle a leaf which is a verde explains rule reference
            if path[-2] == 'verde_rule_directive' and path[-1] == '$ref':
                # We want the domain path from the referenced path. That's every other element after json preamble.
                # e.g. '#/properties/user/properties/quality_of_life' -> ['user','quality_of_life']
                ref_path = '.'.join(d['$ref'].split('/')[2:][::2])
                logging.debug('EXPLAINS EDGE FROM ' + '.'.join(prev_dom_path) + ' TO ' + ref_path)
                v = None  # walk no further, this is just a cross-reference we don't need to expand

            if len(prev_dom_path) > 0 and path[-2] == 'properties':  # don't attempt edge for first node processed
                logging.debug('STANDARD EDGE FROM ' + '.'.join(prev_dom_path) + ' TO ' + '.'.join(dom_path))

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

    with open(domain_schema_file_path, 'r') as f:
        schema = json.load(f)

    logging.info('Processing properties in schema {}'.format(domain_schema_file_path))
    walk(schema['properties'])


def visualise_graph(graph):
    pass


def create_asp_for_explains(domain_schema_file_path, input_mapping_file_path, schema_asp):
    pass


if __name__ == "__main__":
    vu.configure_logger('rule_explains.log', level=logging.DEBUG)
    build_domain_graph('../schemas/verde_asc_domain_schema.json')
