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
                # this fact states the association of a sort order to the field
                lp.append(f'fieldcustomsortorder(\"{field}\", \"{custom_sort}\").')

    # this rule determine that a custom order exists provided the resulting draco encoding is nominal or ordinal.
    lp.append('verde_ordinal_sort(V,E,C,F,O) :- fieldcustomsortorder(F,O), field(V,E,F), '
              'type(V,E,(nominal;ordinal)), channel(V,E,C).')
    # and this show signals that we need to add the custom sort order to the vega-lite spec.
    lp.append('#show verde_ordinal_sort/5.')
    # add a zero weighted soft rule so we can easily spot our custom sort order in the violation comparisons
    # against the baseline specs.
    lp.append('soft(verde_ordinal_sort,V,E):- verde_ordinal_sort(V,E,C,F,O).')
    lp.append('#const verde_ordinal_sort_weight = 0.')
    lp.append('soft_weight(verde_ordinal_sort, verde_ordinal_sort_weight).')
    # TODO investigate how to force drao to treat at ordinal. at present we post-fix the encoding type.
    return lp


"""
% verde rule 03: adding custom sort orders for ordinals
fieldcustomsortorder("Setting", "['community', 'home', 'residential home', 'nursing home']").
custom_ordinal_sort(V,E,C,F,O) :- fieldcustomsortorder(F,O), field(V,E,F), type(V,E,(nominal;ordinal)), channel(V,E,C).
#show custom_ordinal_sort/5.
soft(custom_ordinal_sort,V,E):- custom_ordinal_sort(V,E,C,F,O).
#const custom_ordinal_sort_weight = 0.
soft_weight(custom_ordinal_sort, custom_ordinal_sort_weight).
"""