# All use of draco and dziban done here
from dziban.mkiv import Chart
import pandas as pd
import os
import src.utils as vutils
import logging
import re
from collections import defaultdict


def get_baseline_schema_query_lp(input_file, query, id, directory, write_lp):

    logging.info('creating baseline schema and query lp')
    # use dziban to construct the schema logic program
    df = pd.read_csv(input_file)
    chart = Chart(df)
    enc_field = defaultdict(dict)

    for encoding_id, query_field in enumerate(query):
        chart = eval(f'chart.{query_field}')
        # get the field names as well
        field_name = re.match(r'field\(.*?\'(.*?)\'', query_field)[1]
        enc_field[f'e{encoding_id}']['source_field'] = field_name

    lp = chart._get_full_query()

    if write_lp:
        lp_file = os.path.join(directory, f'{id}_baseline_schema_query.lp')
        vutils.write_list_to_file(lp, lp_file, 'baseline schema and query lp')

    return lp, enc_field


def get_base_view():

    return Chart.DEFAULT_NAME
