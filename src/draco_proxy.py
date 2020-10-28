"""
draco_proxy.py

Marshals all calls to Draco. Includes some pre and post processing to
account for vega-lite properties we have added that are not supported
by draco's asp2vl javascript.
"""

from dziban.mkiv import Chart
from draco.run import run as draco
import pandas as pd
import os
import src.utils as vutils
import logging
import re
import json
from addict import Dict


def get_baseline_schema_query_lp(input_file, query, id, directory, write_lp):

    """
    Use to draco to get the basic fields, types and cardinality, along with the query fields.
    :param input_file:
    :param query:
    :param id:
    :param directory:
    :param write_lp:
    :return:
    """

    logging.info('creating baseline schema and query lp')
    # use dziban to construct the schema logic program
    df = pd.read_csv(input_file)
    chart = Chart(df)

    # repeatedly add the fields to the dziban Chart object
    query_fields = []
    for query_line in query:
        chart = eval(f'chart.{query_line}')
        # get the field names as well
        field_name = re.match(r'field\(.*?\'(.*?)\'', query_line)[1]
        if field_name not in df.columns:
            logging.fatal(f'query field {field_name} is not found in {input_file}')
            exit(1)
        query_fields.append(field_name)

    lp = chart._get_full_query()

    if write_lp:
        lp_file = os.path.join(directory, f'{id}_baseline_schema_query.lp')
        vutils.write_list_to_file(lp, lp_file, 'baseline schema and query lp')

    return lp, query_fields


def run_draco(query, lp_files, num_models):

    """
    :param query:
    :param lp_files:
    :param num_models:
    :return: draco result set
    """
    return draco(query, files=lp_files, topk=True, k=num_models, silence_warnings=True)


def get_vega_lite_spec(result):

    """
    Get a vega-lite spec from the properties returned by clingo.
    Basically a wrapper around draco's asp2vl.js, but that will
    not handle the new properties introduced by verde so we need
    to do some pre and post processing.
    :param result: draco result object
    :return: json vega-lite spec
    """

    view = get_default_view()

    # handle new verde props (e.g. ordinal sort) that asp2vl will baulk at. Should really extend draco asp2vl!
    custom_sorts = [p for p in result.props[view] if p.startswith('verde_ordinal_sort')]
    enc_colour_schemes = [p for p in result.props[view] if p.startswith('verde_color_enc_scheme')]
    double_enc_colour_schemes = [p for p in result.props[view] if p.startswith('verde_color_double_enc_scheme')]
    mark_colours = [p for p in result.props[view] if p.startswith('verde_color_mark')]
    result.props[view] = [p for p in result.props[view] if not p.startswith('verde')]

    logging.debug(f'found {len(custom_sorts)} custom sorts')
    logging.debug(f'found {len(enc_colour_schemes)} encodings of the colour channel')
    logging.debug(f'found {len(double_enc_colour_schemes)} double encodings')
    logging.debug(f'found {len(mark_colours)} mark colours')

    # use draco to get the base spec
    spec = Dict(result.as_vl(view))

    # post-process the vega-lite spec to add in any custom sorts

    # get parts from custom_ordinal_sort(view,encoding,field,custom_sort_value_list)
    regex = re.compile(r'\((.*?),(.*?),(.*?),\"(.*?)\",\"(.*?)\"\)')

    for custom_sort in custom_sorts:
        view, encoding, channel, field, sort_values = re.search(regex, custom_sort).groups()
        sort_values = sort_values.replace('\'', '\"')
        sort_values = json.loads(sort_values)
        spec['encoding'][channel]['sort'] = sort_values
        # TODO spec['encoding'][channel]['type'] = 'ordinal' ... which will impact compare.compare_specs()

    # get parts from verde_color_(double)_enc_scheme(view,encoding,field,field_type,scheme,distance)
    regex = re.compile(r'\((.*?),(.*?),\"(.*?)\",(.*?),\"(.*?)\",(.*?)\)')

    for colour_scheme in enc_colour_schemes + double_enc_colour_schemes:
        view, encoding, field, field_type, scheme, distance = re.search(regex, colour_scheme).groups()
        scheme = json.loads(scheme)
        spec['encoding']['color']['field'] = field
        spec['encoding']['color']['type'] = field_type
        spec['encoding']['color']['scale'] = scheme

    # get parts from verde_color_mark(view,color,distance)
    regex = re.compile(r'\((.*?),\"(.*?)\",(.*?)\)')

    for mark_colour in mark_colours:  # should only be one!
        view, color, distance = re.search(regex, mark_colour).groups()
        color = json.loads(color)
        mark_type = spec['mark']  # draco uses string shorthand for the mark prop, we extend to dict longhand
        spec.pop('mark', None)
        spec['mark']['type'] = mark_type
        spec['mark'].update(color)

    # put the props back
    result.props[view] = result.props[view] + custom_sorts + enc_colour_schemes + \
                         double_enc_colour_schemes + mark_colours

    return spec


def get_default_view():

    """
    We only ever deal with a single view (unlike Dziban), so view is always v_v
    :return: v_v
    """

    return Chart.DEFAULT_NAME
