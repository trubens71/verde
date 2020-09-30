import src.utils as vutils
import src.draco_proxy as vdraco
import src.domain_rule_01_causal as vrule01
import src.domain_rule_02_precision as vrule02
import logging
import json
import os
from addict import Dict


def create_verde_rules_lp(schema_file, mapping_file, query_fields, trial_id, directory, rule_config, baseline_lp):

    logging.info(f'creating verde rules lp based on {schema_file} and {mapping_file}')

    context = Dict()
    context.id = trial_id
    context.directory = directory
    context.rule_config = rule_config

    # Load the input mapping json
    with open(mapping_file) as f:
        mapping_json = json.load(f)

    lp = []
    # Apply each verde rule to extend the lp
    if rule_config.rule_01_causal_relationships.do:
        # ignore previous lp as we are floating fields across encodings
        lp = vrule01.rule_01_causal_relationships(context, schema_file, mapping_json, query_fields)
    else:
        logging.warning('verde rule_01v03_causal_relationships is disabled in config')

    if rule_config.rule_02_data_precision.do:
        lp = lp + vrule02.rule_02_data_precision(context, mapping_json, query_fields)
    else:
        logging.warning('verde rule_02_data_precision is disabled in config')

    # Write out the partial lp containing the data schema and our verde soft rules
    if rule_config.write_lp:
        lp_file = os.path.join(directory, f'{context.id}_verde_schema_query.lp')
        vutils.write_list_to_file(baseline_lp + lp, lp_file, 'verde full schema and query lp')

    return baseline_lp + lp


def bind_fields_to_encodings(fields):
    """
    Binds each field in query to an encoding in the base query.
    :param fields: dictionary of encodings and fields
    :return: a logic program of form: field(v_v,e0,"Displacement").
    """

    lp = ['\n% verde generated logic program','% binding fields to encodings']
    base_view = vdraco.get_default_view()
    for encoding_id in sorted(fields.keys()):
        lp.append(f'field({base_view},{encoding_id},"{fields[encoding_id]["source_field"]}").')
    return lp
