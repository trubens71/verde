import logging
import src.domain_rule_01_causal as vrule01


def rule_03_ordinal(context, schema_file, mapping_json, query_fields):

    logging.info('applying verde rule 03 (custom ordinal sort order))')
    lp = ['\n% verde rule 03: adding custom sort orders for ordinals']

    # get domain nodes with their ordinal sort orders, borrowing from rule01 code.
    domain_node_ordinals = vrule01.get_schema_nodes_and_edges(schema_file, for_rule='rule03')

    # we will add draco rules for all mapped fields, not just the query fields,
    # in case draco introduces additional fields
    mapped_fields = [m['column_name'] for m in mapping_json]

    # get the mapped nodes for each field, borrowing from rule01 code
    field_nodes = vrule01.get_schema_nodes_for_source_fields(mapped_fields, mapping_json)

    for i, field in enumerate(field_nodes.keys()):
        for j, node in enumerate(field_nodes[field]['schema_nodes']):
            if node in domain_node_ordinals:
                custom_sort = domain_node_ordinals[node].__repr__()
                if j > 0:
                    logging.warning(f'found multiple possible sort orders for field {field}, '
                                    f'overriding with this one...')
                logging.info(f'adding custom sort for field {field} due to node {node} with order {custom_sort}')
                # this fact states the relationship between the field and its sort order
                lp.append(f'fieldcustomsortorder(\"{field}\", \"{custom_sort}\").')

    # this rule determine that a custom order exists provided the resulting draco encoding is nominal or ordinal.
    lp.append('custom_ordinal_sort(V,E,F,O) :- fieldcustomsortorder(F,O), field(V,E,F), type(V,E,(nominal;ordinal)).')
    # and this show signals that we need to add the custom sort oder in the vega-lite spec.
    lp.append('#show custom_ordinal_sort/4.')
    return lp


"""
fieldcustomsortorder("Setting", "['tom','dick','harry']").
custom_ordinal_sort(V,E,F,O) :- fieldcustomsortorder(F,O), field(V,E,F), type(V,E,(nominal;ordinal)).
#show custom_ordinal_sort/4.
"""