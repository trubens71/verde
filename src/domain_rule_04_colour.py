"""
Verde rule 04 adds colour schemes and mark colours, where specified in the domain model.
"""

import logging
import src.domain_rule_01_causal as vrule01
import src.utils as vutils


def rule_04_colour(context, schema_file, mapping_json):

    """
    Uses rule01 code to walk the domain model, pulling out colour directives; then getting the field to node
    mappings. Writes field-based asp rules with directives, for mark colours and colour schemes.
    :param context:
    :param schema_file:
    :param mapping_json:
    :return:
    """

    logging.info('applying verde rule 04 (colour)')

    # get domain nodes with their colour directives, borrowing from rule01 code.
    domain_node_colours = vrule01.get_schema_nodes_and_edges(schema_file, for_rule='rule04')

    # we will add draco rules for all mapped fields, not just the query fields,
    # in case draco introduces additional fields
    mapped_fields = [m['column_name'] for m in mapping_json]

    # get the mapped nodes for each field, borrowing from rule01 code
    field_nodes = vrule01.get_schema_nodes_for_source_fields(mapped_fields, mapping_json)

    field_mark_colour = {}
    field_colour_scheme = {}

    # iterate over the fields to find appropriate nearest colours in the domain model.
    for i, field in enumerate(field_nodes.keys()):
        for j, node in enumerate(field_nodes[field]['schema_nodes']):
            mark_colour, distance = find_nearest_colour(domain_node_colours, node, prop='mark_colour')
            if mark_colour:
                if field in field_mark_colour:
                    logging.warning(f'found multiple possible mark colours for {field}'
                                    f'overriding with {mark_colour}')
                field_mark_colour[field] = {'colour': mark_colour, 'distance': distance}
            colour_scheme, distance = find_nearest_colour(domain_node_colours, node, prop='scheme')
            if colour_scheme:
                if field in field_colour_scheme:
                    logging.warning(f'found multiple possible colour schemes for {field}'
                                    f'overriding with {colour_scheme}')
                field_colour_scheme[field] = {'scheme': colour_scheme, 'distance': distance}

    template = vutils.get_jinja_template(context.verde_rule_template_dir,
                                         context.rule_config.rule_04_entity_colours.template)

    return template.render(field_mark_colour=field_mark_colour,
                           field_colour_scheme=field_colour_scheme)


def find_nearest_colour(domain_node_colours, node, prop):

    """
    Iterate over the domain nodes with colour directives, looking for the
    closest match for colour properties. If there is no colour props for the node
    we will take the closest available parent node's colours (ie. we inherit)
    e.g. if we have colours for funder.org_unit, and our node of interest is
    funder.org_unit.nhs_org_unit for which there is no colour, then we'll take the
    colour of funder.org_unit

    :param domain_node_colours: dictionary of domain nodes to colour props
    :param node: the node we are offering up.
    :param prop: either mark_colour or scheme
    :return:
    """

    prop_value = None
    distance = None

    for domain_node in sorted(domain_node_colours):  # sorting then overriding takes care of inheritance...
        if domain_node == node[0:len(domain_node)]:  # ... provided we work on partial match
            if prop in domain_node_colours[domain_node]:
                prop_value = domain_node_colours[domain_node][prop]
                distance = node.count('.') - domain_node.count('.')  # bit sneaky but works!

    return prop_value, distance
