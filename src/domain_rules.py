"""
domain_rules.py

Orchestrates the generation of Verde rules

Entry point: create_verde_rules_lp()
"""

import src.utils as vutils
import src.draco_proxy as vdraco
import src.domain_rule_01_causal as vrule01
import src.domain_rule_02_precision as vrule02
import src.domain_rule_03_ordinal as vrule03
import src.domain_rule_04_colour as vrule04
import logging
import json
import os
from addict import Dict


def create_verde_rules_lp(schema_file, input_file, mapping_file,
                          query_fields, trial_id, directory, rule_config, baseline_lp,
                          verde_rule_template_dir):
    """
    Works through each implemented verde rule.
    :param schema_file:
    :param input_file:
    :param mapping_file:
    :param query_fields:
    :param trial_id:
    :param directory:
    :param rule_config:
    :param baseline_lp:
    :param verde_rule_template_dir:
    :return:
    """

    logging.info(f'creating verde rules lp based on {schema_file} and {mapping_file}')

    context = Dict()
    context.id = trial_id
    context.directory = directory
    context.rule_config = rule_config
    context.verde_rule_template_dir = verde_rule_template_dir

    # Load the input mapping json
    with open(mapping_file) as f:
        mapping_json = json.load(f)

    lp_str = ""
    # Apply each verde rule to extend the lp
    if rule_config.rule_01_causal_relationships.do:
        lp_str += vrule01.rule_01_causal_relationships(context, schema_file, mapping_json, query_fields)
    else:
        logging.warning('verde rule_01_causal_relationships is disabled in config')

    if rule_config.rule_02_data_precision.do:
        lp_str += vrule02.rule_02_data_precision(context, mapping_json, query_fields)
    else:
        logging.warning('verde rule_02_data_precision is disabled in config')

    if rule_config.rule_03_ordinal_sort.do:
        lp_str += vrule03.rule_03_ordinal_sort(context, schema_file, input_file, mapping_json, query_fields)
    else:
        logging.warning('verde rule_03_ordinal_sort is disabled in config')

    if rule_config.rule_04_entity_colours.do:
        lp_str += vrule04.rule_04_colour(context, schema_file, mapping_json)
    else:
        logging.warning('verde rule_04_entity_colours is disabled in config')

    lp = lp_str.split('\n')  # bit messy, we used lists elsewhere then moved to jinja templates

    # Write out the partial lp containing the data schema and our verde soft rules
    if rule_config.write_lp:
        lp_file = os.path.join(directory, f'{context.id}_verde_schema_query.lp')
        vutils.write_list_to_file(baseline_lp + lp, lp_file, 'verde full schema and query lp')

    return baseline_lp + lp

