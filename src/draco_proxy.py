# All use of draco and dziban done here
from dziban.mkiv import Chart
import pandas as pd
import os
import src.utils as vutils
import logging


def get_draco_schema_query_lp(input_file, query, id, directory, write_lp):

    # THIS WORKS FOR VANILLA DRACO, BUT...
    # - whilst we need this for comparison,
    # - the verde asp form is different, per our cars exploration,
    # - so how do we have a common query format in the yaml and handle both cases?
    #   - re-implement dziban logic, or...
    #   - fix the dziban generated lp?

    logging.info('creating schema and query lp')
    # use dziban to construct the schema logic program
    df = pd.read_csv(input_file)
    chart = Chart(df)

    local_vars = {'chart', chart}
    for query_field in query:
        chart = eval(f'chart.{query_field}')

    lp = chart._get_full_query()

    if write_lp:
        lp_file = os.path.join(directory, f'{id}_schema_query.lp')
        vutils.write_list_to_file(lp, lp_file, 'schema and query lp')
    return lp
