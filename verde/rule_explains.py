import verde.verde_utils as vu
import logging
import json


def build_domain_graph(domain_schema_file_path):

    def walk(d, path=None, dom_path=None):

        if path is None:  # full technical path
            path = ['properties']
        if dom_path is None:  # domain specific terms only, no json schema reserved words
            dom_path = []

        for k, v in d.items():

            path.append(k)
            prev_dom_path = dom_path.copy()

            if k == '$ref':  # dig into the original schema to instantiate the reference
                nonlocal schema
                schema_part = schema
                for node in v.split('/')[1:]:  # ignore leading '#'
                    schema_part = schema_part[node]
                pass
                v = schema_part

            if k == 'verde_rule_directive':
                pass
                #logging.warning('need to deal with verde_rule_directive')

            if path[-2] == 'properties':  # all domain specific terms will be properties
                dom_path.append(k)

            if len(prev_dom_path) > 0 and path[-2] == 'properties':
                logging.debug('EDGE FROM ' + '.'.join(prev_dom_path) + ' TO ' + '.'.join(dom_path))

            if isinstance(v, dict):
                walk(v, path, dom_path)
            elif isinstance(v, list):
                for v_item in v:
                    if isinstance(v_item, dict):
                        walk(v_item, path, dom_path)

            if path[-2] == 'properties':
                dom_path.pop()

            path.pop()

    with open(domain_schema_file_path, 'r') as f:
        schema = json.load(f)

    logging.info('Processing definitions in schema {}'.format(domain_schema_file_path))
    walk(schema['definitions'])
    #walk(schema['properties'])


def visualise_graph(graph):
    pass


def create_asp_for_explains(domain_schema_file_path, input_mapping_file_path, schema_asp):
    pass


if __name__ == "__main__":
    vu.configure_logger('rule_explains.log', level=logging.DEBUG)
    build_domain_graph('../schemas/verde_asc_domain_schema.json')
