import logging
import src.draco_proxy as vdraco
import os
import glob


def get_vis_results(trial_id, directory, input_data_file, query,
                    base_lp_dir, override_lp_dir=None, num_models=10):

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
        logging.info(f'getting draco visualisations for {trial_id} with verde base lp override')
        lp_files = get_overridden_lp_files(base_lp_dir, override_lp_dir)
    else:
        logging.info(f'getting draco visualisations for {trial_id}')
        lp_files = get_lp_files(base_lp_dir, 'base')

    pass
    results = vdraco.run_draco(query, lp_files, num_models)

    return results


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

    logging.info(f'overrode {n_override} lp files and added {n_added}')

    # return the full paths
    return file_dict.values()


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


get_overridden_lp_files('../asp/draco_base', '../asp/verde_override')