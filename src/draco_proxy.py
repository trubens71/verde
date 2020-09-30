# All use of draco and dziban done here
from dziban.mkiv import Chart
from draco.run import run as draco
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

    # repeatedly add the fields to the dziban Chart object
    query_fields = []
    for query_line in query:
        chart = eval(f'chart.{query_line}')
        # get the field names as well
        field_name = re.match(r'field\(.*?\'(.*?)\'', query_line)[1]
        query_fields.append(field_name)

    lp = chart._get_full_query()

    if write_lp:
        lp_file = os.path.join(directory, f'{id}_baseline_schema_query.lp')
        vutils.write_list_to_file(lp, lp_file, 'baseline schema and query lp')

    return lp, query_fields


def run_draco(query, lp_files, num_models):

    return draco(query, files=lp_files, topk=True, k=num_models, silence_warnings=True)


def get_default_view():

    return Chart.DEFAULT_NAME
