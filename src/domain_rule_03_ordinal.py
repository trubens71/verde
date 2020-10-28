"""
domain_rule_03_ordinal.py

Verde rule 03 adds custom sort orders, where specified in the domain model.

Entry point:  rule_03_ordinal()
"""

import logging
import src.domain_rule_01_causal as vrule01
import src.domain_rule_03_ordinal_nlp as vrule03nlp
import src.utils as vutils
from addict import Dict
import pandas as pd

custom_sort_cache = Dict()


def rule_03_ordinal_sort(context, schema_file, input_file, mapping_json, query_fields):

    """
    Uses rule01 code to walk the domain model, pulling out sort directives; then getting the field to node
    mappings. Writes field-based asp rules with directives.
    :param context:
    :param schema_file:
    :param input_file:
    :param mapping_json:
    :param query_fields:
    :return:
    """

    logging.info('applying verde rule 03 (custom ordinal sort order))')
    lp = ['\n% verde rule 03: adding custom sort orders for ordinals']

    # get domain nodes with their ordinal sort orders, borrowing from rule01 code.
    domain_node_ordinals = vrule01.get_schema_nodes_and_edges(schema_file, for_rule='rule03')

    # we will add draco rules for all mapped fields, not just the query fields,
    # in case draco introduces additional fields
    mapped_fields = [m['column_name'] for m in mapping_json]

    # get the mapped nodes for each field, borrowing from rule01 code
    field_nodes = vrule01.get_schema_nodes_for_source_fields(mapped_fields, mapping_json)

    field_custom_sort = {}

    for i, field in enumerate(field_nodes.keys()):
        for j, node in enumerate(field_nodes[field]['schema_nodes']):
            if node in domain_node_ordinals:
                # custom_sort = domain_node_ordinals[node].__repr__()
                custom_sort = get_custom_sort_order(input_file, field,
                                                    node, domain_node_ordinals[node]).__repr__()
                if j > 0:
                    logging.warning(f'found multiple possible sort orders for field {field}, '
                                    f'overriding with this one...')
                logging.info(f'adding custom sort for field {field} due to node {node} with order {custom_sort}')
                field_custom_sort[field] = custom_sort

    template = vutils.get_jinja_template(context.verde_rule_template_dir,
                                         context.rule_config.rule_03_ordinal_sort.template)

    return template.render(field_custom_sort=field_custom_sort)


def get_custom_sort_order(source_data_file, field, domain_node, domain_ordinal_terms):
    """
    Returns the unique values of a field in an input data file, sorted by
    similarity to ordinal domain terms. Determining the unique vales and
    The NLP processing is expensive, so results are cached for use in subsequent
    mappings and experiments.
    :param domain_node:
    :param source_data_file:
    :param field:
    :param domain_ordinal_terms:
    :return:
    """

    global custom_sort_cache
    cache = custom_sort_cache

    if source_data_file not in custom_sort_cache:
        custom_sort_cache[source_data_file] = get_field_unique_values(source_data_file)
    else:
        logging.debug(f'cache hit for unique field values in {source_data_file}')

    field_unique_values = custom_sort_cache[source_data_file][field]['unique_values']

    if domain_node not in custom_sort_cache.source_data_file.field.nodes:
        custom_sort_cache[source_data_file][field]['sort_by_nodes'] = \
            {domain_node: vrule03nlp.order_source_data_terms(field_unique_values, domain_ordinal_terms)}
    else:
        logging.debug(f'cache hit for custom sort for field {field} based on node {domain_node}')

    return custom_sort_cache[source_data_file][field]['sort_by_nodes'][domain_node]


def get_field_unique_values(source_data_file):
    """
    Find unique field values in a csv file, where they are string-like
    :param source_data_file:
    :return: dictionary of field to unique values
    """
    logging.info(f'getting unique values of fields in {source_data_file}')
    column_values = Dict()
    df = pd.read_csv(source_data_file)
    df = df.select_dtypes(include=['object'])  # select the columns containing string data

    for column in df.columns:
        column_values[column]['unique_values'] = list(df[column].unique())

    return column_values
