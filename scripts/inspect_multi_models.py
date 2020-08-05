import verde.verde_utils as vu
import logging
import json
from draco.run import Result
from clyngor.answers import Answers
import sys
import os

"""
Takes multi-model output json from clingo (with --outf=2, --quiet=0,0,2).
Outputs n lowest cost VL specs in one file
"""

no_pref_file = 'full_no_pref.json'
with_pref_file = 'full_with_pref.json'
with_pref_adj_weight_file = 'full_with_pref_adjweight.json'


def process_clingo_json_file(input_file_name, max_models=10):

    logging.info(f'processing clingo output from {input_file_name} for up to {max_models} models')
    with open(input_file_name) as f:
        clingo_json = json.load(f)

    output_json = []

    for answer in clingo_json["Call"][0]["Witnesses"][:-max_models-1:-1]:
        result = Result(Answers(answer["Value"]).sorted, cost=answer['Costs'][0])
        vl = result.as_vl()
        output_json.append({'cost': result.cost, 'vega-lite': vl})

    output_file_name = input_file_name.split('.json')[0] + '_vl.json'
    logging.info(f'writing costs and vega-lite for {len(output_json)} models')
    with open(output_file_name, 'w') as f:
        json.dump(output_json, f)


if __name__ == "__main__":
    logging = vu.configure_logger('inspect_multi_models.log', logging.DEBUG)
    if len(sys.argv) == 0:
        input_file = with_pref_adj_weight_file
    else:
        input_file = sys.argv[1]
        if not os.path.isfile(input_file):
            logging.fatal(f'input file {input_file} not found')
            exit(1)

    process_clingo_json_file(input_file)




