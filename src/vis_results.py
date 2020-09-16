import logging
import src.draco_proxy as vdraco
import os
import glob
import json
import src.utils as vutils


def get_vis_results(trial_id, directory, input_data_file, query,
                    base_lp_dir, override_lp_dir=None, num_models=10, label='', write_lp=True):

    """
    Run draco then capture store the resulting visualisation details.
    :param write_lp:
    :param label: just used for logging text, probably baseline or verde.
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

    if write_lp:
        write_full_lp(trial_id, directory, label, lp_files, query)

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


def write_full_lp(trial_id, directory, label, lp_files, query):

    """
    write out the full lp in case we want to run it through clingo manually
    :param trial_id:
    :param directory:
    :param lp_files:
    :param query:
    :return:
    """

    lp = []

    for file_name in lp_files:
        with open(file_name) as f:
            lp.append(f.read())

    lp = lp + query
    output_file_name = os.path.join(directory, f'{trial_id}_{label}_full.lp')
    vutils.write_list_to_file(lp, output_file_name, f'{label} full lp')


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
    :param label:
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
        vl_spec_file = f'{trial_id}_{label}_m{i:02}_c{model["cost"]:03}_vl.json'
        title = os.path.splitext(vl_spec_file)[0]
        model['vl']['title'] = title
        with open(os.path.join(vl_dir, vl_spec_file), 'w') as f:
            json.dump(model['vl'], f)


def make_vegalite_concat(trial_id, directory, json_results_list, labels):

    """
    create a concatenated vega-lite spec for the results.
    :param labels:
    :param trial_id:
    :param directory:
    :param json_results_list:
    :return:
    """
    vl = {'$schema': json_results_list[0][0]['vl']['$schema'],
          'data': {'url': json_results_list[0][0]['vl']['data']['url']},
          'title': {'text': trial_id, 'anchor': 'middle'},
          'hconcat': []}

    # if passed multiple results sets then we arrange them in columns
    for json_result, label in zip(json_results_list, labels):
        row_specs = []
        for i, model in enumerate(json_result):
            spec = model['vl']
            spec.pop('$schema', None)
            spec.pop('data', None)
            spec['title'] = f'{label} model {i:03} cost {model["cost"]}'
            row_specs.append(spec)
        vl['hconcat'].append({'vconcat': row_specs})

    vl_output_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_vl.json')

    logging.info(f'writing concat vegalite results to {vl_output_file}')
    with open(vl_output_file, 'w') as f:
        json.dump(vl, f)

    # create a vega-embed html file...

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Verde ranked visualisation view</title>
          <!-- Import Vega & Vega-Lite (does not have to be from CDN) -->
        <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
        <!-- Import vega-embed -->
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    </head>
    <body>
        <div id="vis"></div>
        <script type="text/javascript">
          var spec = "VIS_SPEC";
          vegaEmbed('#vis', spec).then(function(result) {}).catch(console.error);
        </script>   
    </body>
    </html>
    """

    html_content = html_content.replace('VIS_SPEC', os.path.basename(vl_output_file))
    html_output_file = os.path.splitext(vl_output_file)[0] + '.html'
    with open(html_output_file, 'w') as f:
        f.write(html_content)