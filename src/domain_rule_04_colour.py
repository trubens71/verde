import logging
import src.domain_rule_01_causal as vrule01
import jinja2 as jj


def rule_04_ordinal(context, schema_file, input_file, mapping_json, query_fields):
    """
    Uses rule01 code to walk the domain model, pulling out colour directives; then getting the field to node
    mappings. Writes field-based asp rules with directives, for mark colours and colour schemes.
    :param context:
    :param schema_file:
    :param input_file:
    :param mapping_json:
    :param query_fields:
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
            mark_colour = find_nearest_colour(domain_node_colours, node, prop='mark_colour')
            if mark_colour:
                if field in field_mark_colour:
                    logging.warning(f'found multiple possible mark colours for {field}'
                                    f'overriding with {mark_colour}')
                field_mark_colour[field] = mark_colour
            colour_scheme = find_nearest_colour(domain_node_colours, node, prop='scheme')
            if colour_scheme:
                if field in field_colour_scheme:
                    logging.warning(f'found multiple possible colour schemes for {field}'
                                    f'overriding with {colour_scheme}')
                field_colour_scheme[field] = colour_scheme

    # TODO now implemented rules via jinja
    pass


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

    prop_value = ''

    for domain_node in sorted(domain_node_colours):  # sorting then overriding takes care of inheritance...
        if domain_node == node[0:len(domain_node)]:  # ... provided we work on partial match
            if prop in domain_node_colours[domain_node]:
                prop_value = domain_node_colours[domain_node][prop]

    return prop_value


"""
rule development
% verde
fieldcolorscheme("Gross_Total_Expenditure_x1000", "{\"scheme\": \"oranges\"}").
fieldmarkcolor("LA_name","{\"color\": \"black\"}").
fieldmarkcolor("Geography_code","{\"color\": \"gray\"}").
fieldmarkcolor("Region_name","{\"color\": \"blue\"}").
fieldcolorscheme("Setting", "{\"scheme\": \"pastel1\"}").

% first case: color channel is used and we have a scheme for the encoding field.
verde_color_enc_scheme(V,E,F,CS) :- fieldcolorscheme(F,CS), field(V,E,F), channel(V,E,color).

% second case: if first case not applied, and we have non-aggregated field encoding for which there is a schema...
verde_color_double_enc_scheme(V,E,F,CS) :- not verde_color_enc_scheme(_,_,_,_), field(V,E,F), not aggregate(V,E,_), discrete(V,E), fieldcolorscheme(F,CS).

% third case: if first two cases does not apply but we have an appropriate mark color
verde_mark_color_choices(V,CO) :- not verde_color_enc_scheme(_,_,_,_), not verde_color_double_enc_scheme(_,_,_,_), view(V), fieldmarkcolor(F,CO), fieldtype(F,FT), FT != "number", cardinality(F,CA), num_rows(NR), CA = NR.
% choose only one
1 { verde_color_mark(V,CO): verde_mark_color_choices(V,CO)} 1 :- verde_mark_color_choices(_,_).

#show verde_color_enc_scheme/4.
#show verde_color_double_enc_scheme/4.
#show verde_color_mark/2.

soft(verde_color_enc_scheme,V,E) :- verde_color_enc_scheme(V,E,F,CS).
soft(verde_color_double_enc_scheme,V,E) :- verde_color_double_enc_scheme(V,E,F,CS).
soft(verde_color_mark,V,CO) :- verde_color_mark(V,CO).

#const verde_color_enc_scheme_weight = 0.
#const verde_color_double_enc_scheme_weight = 0.
#const verde_color_mark_weight = 0.

soft_weight(verde_color_enc_scheme, verde_color_enc_scheme_weight).
soft_weight(verde_color_double_enc_scheme, verde_color_double_enc_scheme_weight).
soft_weight(verde_color_mark, verde_color_mark_weight).

"""
"""
Draco colour rules.

They all relate to use of the colour channel, therefore conclude that
colour and schema choices are deferred to vega-lite

% @constraint Prefer not to use high cardinality nominal for color.
soft(high_cardinality_nominal_color,V,E) :- type(V,E,nominal), channel(V,E,color), enc_cardinality(V,E,C), C > 10.
#const high_cardinality_nominal_color_weight = 10.

% @constraint Continuous on color channel.
soft(continuous_color,V,E) :- channel(V,E,color), continuous(V,E).
#const continuous_color_weight = 10.

% @constraint Ordered on color channel.
soft(ordered_color,V,E) :- channel(V,E,color), discrete(V,E), not type(V,E,nominal).
#const ordered_color_weight = 8.

% @constraint Nominal on color channel.
soft(nominal_color,V,E) :- channel(V,E,color), type(V,E,nominal).
#const nominal_color_weight = 6.

There are other colour rules related to entropy, interesting, value/summary task, which we do not encounter.
Those are still concerned with encoding the colour channel.
"""