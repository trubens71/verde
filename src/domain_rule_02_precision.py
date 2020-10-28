"""
domain_rule_02_precision.py

Verde rule 02 uses the strength of the data as specified in the input data domain mapping document,
and states channel encoding preferences. So imprecise data (e.g. from a survey) will not compete
with a stronger field for a more effective channel.

Entry point: rule_02_data_precision()
"""


import logging
import itertools
from collections import defaultdict
import src.utils as vutils


def rule_02_data_precision(context, mapping_json, query_fields):
    """
    For each pair of fields and each pair of channels, write rules based on strength of field data.
    Each field in the mapping json will either have a strength between zero and one, for example fields from survey data
    will have a low strength than those from administrative systems. We will assign an imprecision to each channel,
    for examples x=0, size=1. Our goal is to write rules which prefer stronger fields on more precise channels.
    :param query_fields:
    :param context:
    :param mapping_json:
    :return:
    """

    logging.info('applying verde rule 02 (data precision))')
    lp = ['\n% verde rule 02: x/y/size/colour encoding preferences based on source field strength']

    channel_imprecision = {
        "x": 0,
        "y": 0,
        "size": 1,
        "color": 2
    }

    def field_strength(f):
        # get the strength or default to 1.0
        return f.get('verde_source_meta', {}).get('strength', 1.0)

    # whilst developing we will limit rules to fields in query.
    mapping_json = [mapping for mapping in mapping_json if mapping['column_name'] in query_fields]

    soft_weight = context.rule_config.rule_02_data_precision.draco_soft_weight or 100

    rules = defaultdict(dict)

    # Process each pair of fields and then each pair of channels
    for i, (field_a, field_b) in enumerate(list(itertools.combinations(mapping_json, 2))):

        if field_strength(field_a) < field_strength(field_b):
            weaker_field, stronger_field = (field_a['column_name'], field_b['column_name'])
        elif field_strength(field_a) > field_strength(field_b):
            weaker_field, stronger_field = (field_b['column_name'], field_a['column_name'])
        else:
            continue  # only need rules for fields of different strength, else we have no preference

        for j, (channel_a, channel_b) in enumerate(list(itertools.combinations(channel_imprecision.keys(), 2))):
            # we only need rules for channels of different precision

            if channel_imprecision[channel_a] < channel_imprecision[channel_b]:
                more_precise_channel, less_precise_channel = (channel_a, channel_b)
            elif channel_imprecision[channel_a] > channel_imprecision[channel_b]:
                more_precise_channel, less_precise_channel = (channel_b, channel_a)
            else:
                continue  # we only need rules for channels of different precision

            logging.info(f"preference is {stronger_field} on {more_precise_channel} "
                         f"and {weaker_field} on {less_precise_channel}")

            # create a soft rule which assigns a cost to not observing our preference
            rule_id = f'rule_02_{i:02}_{j:02}'
            rules[rule_id]['stronger_field'] = stronger_field
            rules[rule_id]['weaker_field'] = weaker_field
            rules[rule_id]['more_precise_channel'] = more_precise_channel
            rules[rule_id]['less_precise_channel'] = less_precise_channel

    template = vutils.get_jinja_template(context.verde_rule_template_dir,
                                         context.rule_config.rule_02_data_precision.template)

    return template.render(rules=rules, channels=channel_imprecision, soft_weight=soft_weight)
