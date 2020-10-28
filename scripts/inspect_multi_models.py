import verde_old.verde_utils as vu
import logging
import json
from draco.run import Result
from clyngor.answers import Answers
import sys
import getopt
import os
import glob
import re

"""
Takes multi-model output json from clingo (with --outf=2, --quiet=0,0,2).
Outputs n lowest cost VL specs in one file, plus violation counts and weights.
"""

no_pref_file = 'full_no_pref.json'
with_pref_file = 'full_with_pref.json'
with_pref_adj_weight_file = 'full_with_pref_adjweight.json'


def process_clingo_json_file(answer_file_name, soft_weights, max_models=10):
    """
    Grab the costs, answers and violated soft constraints from an answer file
    :param soft_weights:
    :param answer_file_name:
    :param max_models:
    :return:
    """
    logging.info(f'processing clingo output from {answer_file_name} for up to {max_models} models')
    with open(answer_file_name) as f:
        clingo_json = json.load(f)

    output_json = []

    # delete previous vl files because the file names include the cost, and therefore changes to the query which
    # result in different models will not over-write the previous run.
    file_pattern = os.path.basename(answer_file_name).split('.json')[0] + '_*_vl.json'
    path_pattern = os.path.join(vl_dir, file_pattern)
    logging.info(f'deleting any prior vl files in {path_pattern}')
    for f in glob.glob(path_pattern):
        os.remove(f)

    for answer in clingo_json["Call"][0]["Witnesses"][:-max_models-1:-1]:
        result = Result(Answers(answer["Value"]).sorted, cost=answer['Costs'][0])
        vl = result.as_vl()
        #  process the violations
        violations = {}
        for k, v in result.violations.items():
            v_details = {'count': v, 'weight': soft_weights[k]}
            violations[k] = v_details
        output_json.append({'cost': result.cost, 'vega-lite': vl, 'violations': violations})
        gen_vl_file(answer_file_name, vl, result.cost )

    output_file_name = answer_file_name.split('.json')[0] + '_inspect.json'
    logging.info(f'writing costs and vega-lite for {len(output_json)} models')
    with open(output_file_name, 'w') as f:
        json.dump(output_json, f)


def get_soft_constraints_and_weights(lp):
    """
    Build a dictionary of all soft constraints in the logic program so we
    can report on those in the answer models
    :param lp:
    :return:
    """
    logging.info(f'getting soft constraint details from {lp}')

    with open(lp) as f:
        lines = f.readlines()

    weights = {}
    sw_pattern = re.compile(r'#const (.*) = ([0-9]+)\.')
    for sw in [l for l in lines if sw_pattern.match(l)]:
        m = sw_pattern.match(sw)
        weights[m.group(1)] = m.group(2)

    softs = {}
    soft_pattern = re.compile(r'soft_weight\((.*),(.*)\).')
    for soft in [l for l in lines if soft_pattern.match(l)]:
        m = soft_pattern.match(soft)
        softs[m.group(1)] = weights[m.group(2)]

    return softs


def gen_vl_file(answer_file_name, spec, cost):

    global vl_dir

    if vl_dir:
        if not os.path.isdir(vl_dir):
            logging.info(f'creating dir {vl_dir} for vl specs')
            os.mkdir(vl_dir)
        vl_file_name = os.path.basename(answer_file_name).split('.json')[0] + f'_{cost:03d}_vl.json'

        with open(os.path.join(vl_dir, vl_file_name), 'w') as f:
            json.dump(spec, f)


if __name__ == "__main__":

    logging = vu.configure_logger('inspect_multi_models.log', logging.DEBUG)

    argv = sys.argv[1:]
    try:
        opt, _ = getopt.getopt(argv, 'l:a:m:v:')
    except getopt.GetoptError as e:
        logging.fatal(f'getopt error {e.msg}')
        sys.exit(1)

    lp_file = ''
    ans_file = ''
    models = 10
    vl_dir = None

    for arg, val in opt:
        if arg == '-l':
            lp_file = val
        if arg == '-a':
            ans_file = val
        if arg == '-m':
            models = val
        if arg == '-v':
            vl_dir = val

    if not os.path.isfile(lp_file):
        logging.fatal(f'logic program {lp_file} not found')
        exit(1)

    if not os.path.isfile(ans_file):
        logging.fatal(f'answer set {ans_file} not found')
        exit(1)

    soft_weights = get_soft_constraints_and_weights(lp_file)

    logging.info(f'processing {lp_file} and {ans_file}')
    process_clingo_json_file(ans_file, soft_weights, max_models=models)




