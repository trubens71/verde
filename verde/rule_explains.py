import verde.verde_utils as vu
import logging
import json


def flatten_explain_directive(dir_dict):
    if 'explains' not in dir_dict:
        return []

    def flatten(p, d):
        if isinstance(d, dict) and len(d) == 0:
            return p
        elif not isinstance(d, dict):
            return p
        result = ''
        for key, value in d.items():
            if len(p) == 0:
                new_p = key
            else:
                new_p = p + '.' + key
            result = flatten(new_p, value)
        return result

    results = []

    for explain_ref in dir_dict['explains']:
        flat_ref = flatten('', explain_ref)
        results.append(flat_ref)

    return results


def build_domain_graph(domain_schema_file_path):
    """
    Take a domain schema json file and build a network graph.
    Creates edges between all associated nodes by merit of their
    schema relationship as well as verde_rule_directives of the
    type 'explains'.
    :param domain_schema_file_path:
    :return: networkx graph
    """

    reserved_words = ['properties', 'type', 'additionalProperties', '$ref', 'oneOf']

    with open(domain_schema_file_path, 'r') as f:
        schema = json.load(f)

    def iterate(parent, dic):

        for key, value in dic.items():
            if len(parent) == 0:
                new_key = key
            else:
                if key == 'verde_rule_directive':
                    for explain_ref in flatten_explain_directive(value):
                        logging.debug('Adding explains edge from {} to {}'.format(parent, explain_ref))
                    break
                elif key == 'domain_meta':
                    pass
                elif key not in reserved_words:
                    new_key = parent + '.' + key
                    logging.debug('Adding edge from {} to {}'.format(parent, new_key))
                else:
                    new_key = parent

            if isinstance(value, dict):
                iterate(new_key, value)

    logging.info('Processing definitions in schema')
    iterate('', schema['definitions'])
    logging.info('Processing properties in schema - not yet following $refs and not filtering out domain_meta (phase)')
    iterate('', schema['properties'])


def visualise_graph(graph):
    pass


def create_asp_for_explains(domain_schema_file_path, input_mapping_file_path, schema_asp):
    pass


if __name__ == "__main__":
    vu.configure_logger('rule_explains.log', level=logging.DEBUG)
    build_domain_graph('../schemas/verde_asc_domain_schema.json')
