import logging
import src.draco_proxy as vdraco
import os
import glob
import json
from vega import VegaLite


def get_vis_results(trial_id, directory, input_data_file, query,
                    base_lp_dir, override_lp_dir=None, num_models=10, label=''):

    """
    Run draco then capture store the resulting visualisation details.
    :param trial_id:
    :param directory:
    :param input_data_file:
    :param query:
    :param base_lp_dir:
    :param override_lp_dir:
    :param num_models:
    :return: result structure tbd
    """

    if override_lp_dir:
        logging.info(f'getting {label} draco visualisations for {trial_id} with verde base lp override')
        lp_files = get_overridden_lp_files(base_lp_dir, override_lp_dir)
    else:
        logging.info(f'getting {label} draco visualisations for {trial_id}')
        lp_files = get_lp_files(base_lp_dir, 'base')

    draco_results = vdraco.run_draco(query, lp_files, num_models)
    if not draco_results:
        logging.fatal(f'no {label} results returned by draco')
        exit(1)

    json_results = write_results_json(trial_id, directory, input_data_file, draco_results, label)
    write_results_vegalite(trial_id, directory, label, json_results)

    return draco_results, json_results


def get_overridden_lp_files(base_dir, override_dir):

    """
    Build a list of draco base lp files with
    :param base_dir: our copy of base draco lp files
    :param override_dir: the base lp files we have hacked a bit
    :return: list of lp files
    """

    # check integrity of parameters
    dirs = zip(['base', 'override'], [base_dir, override_dir])
    for label, directory in dirs:
        if directory is None or not os.path.isdir(directory):
            logging.fatal(f'cannot find {label} lp directory: {directory}')
            exit(1)

    # collect the base files with file name versus full path
    file_dict = {}
    for file in get_lp_files(base_dir, 'base'):
        file_dict[os.path.basename(file)] = file

    # override using the file name not the full path
    n_override = 0
    n_added = 0
    for file in get_lp_files(override_dir, 'override'):
        if os.path.basename(file) in file_dict:
            n_override += 1
        else:
            n_added += 1
        logging.debug(f'adding verde base lp file {file}')
        file_dict[os.path.basename(file)] = file

    logging.info(f'overrode {n_override} base lp files and added {n_added} lp files')

    # return the full paths
    return sorted(list(file_dict.values()))


def get_lp_files(directory, label=''):

    """
    get a list of lp files
    :param directory:
    :param label: just for logging purposes
    :return: list of fies
    """

    files = sorted(glob.glob(f'{directory}/*.lp'))

    if not len(files):
        logging.warning(f'no {label} lp files found in {directory}')

    return files


def write_results_json(trial_id, directory, input_data_file, results, label):

    """
    write a single results json file with costs, etc. Then separate visualisations.
    :param trial_id:
    :param directory:
    :param input_data_file:
    :param results:
    :param label:
    :return: results
    """
    results_json = []

    for result in results:

        # organise the soft rule violation counts and weights
        violations = {}
        for rule in sorted(result.violations.keys()):
            violations[rule] = {
                'num': result.violations[rule],
                'weight': result.draco_weights[rule],
                'cost_contrib:': int(result.violations[rule] * result.draco_weights[rule])
            }

        # get the cost and add in the violations
        model = {'cost': result.cost,
                 'violations': violations,
                 'props': result.props[vdraco.get_default_view()]}

        # get the vega-lite spec
        vl = result.as_vl(vdraco.get_default_view())
        # hack because draco's asp2vl defaults to the cars data set!
        vl['data']['url'] = os.path.join('../data', os.path.basename(input_data_file))
        model['vl'] = vl

        results_json.append(model)

    results_file = os.path.join(directory, f'{trial_id}_{label}_results.json')
    logging.info(f'writing {label} results to {results_file}')
    with open(results_file, 'w') as f:
        json.dump(results_json, f)

    return results_json


def write_results_vegalite(trial_id, directory, label, json_results):

    """
    write the vl spec to a vis sub-directory
    :param trial_id:
    :param directory:
    :param json_results:
    :return:
    """

    vl_dir = os.path.join(directory,'vegalite')
    # make the sub-dir if necessary
    if not os.path.isdir(vl_dir):
        os.mkdir(vl_dir)

    # write the spec and image for each model
    logging.info(f'writing {label} vega-lite specs to {vl_dir}')
    for i, model in enumerate(json_results):
        vl_spec_file = f'{trial_id}_{i:02}_{model["cost"]:03}_vl.json'
        with open(os.path.join(vl_dir, vl_spec_file), 'w') as f:
            json.dump(model['vl'], f)
