"""
Main script to execute a verde trial based on a config file trial.yaml in a specified directories
"""

import sys
import src.utils as vutils
from src.trial import Trial
import logging
import os

TRIAL_YAML = 'trial.yaml'
TRIAL_SCHEMA = '../schemas/verde_trial_schema.json'


def run_trial(directory):

    """
    runs a single triel
    :param directory:
    :return:
    """

    experiments_ran = []
    trial = Trial(directory, TRIAL_YAML)

    for exp in trial.experiments:
        if exp.do:
            exp.run()
            experiments_ran.append(exp.id)
        else:
            logging.warning(f'{exp.experiment_id} is disabled in config')
    trial.exec_regression_test()

    logging.info(f'Completed experiments {experiments_ran}')


def trial_yaml_files_exist(dirs):

    """
    Make sure all dirs from command line exist and have a trial.yaml file.
    :param dirs: list of directories
    :return: config_ok boolean
    """

    config_ok = True

    if not os.path.exists(TRIAL_SCHEMA):
        logging.fatal(f'cannot find trial config schema {TRIAL_SCHEMA}')

    for d in dirs:
        trial_yaml_config_file = f'{d}/{TRIAL_YAML}'
        if not os.path.isdir(d):
            logging.fatal(f'directory {d} not found')
            config_ok = False
        elif not os.path.isfile(trial_yaml_config_file):
            logging.fatal(f'no {TRIAL_YAML} found in {d}')
            config_ok = False
        elif not vutils.validate_json_doc(trial_yaml_config_file, TRIAL_SCHEMA):
            logging.fatal(f'{trial_yaml_config_file} failed validation against {TRIAL_SCHEMA}')
            config_ok = False

    return config_ok


if __name__ == "__main__":

    """
    Run trials based on a list of trial directories passed on the command line.
    Each directory must have a trial.yaml file in it.
    """

    logging = vutils.configure_logger('verde.log', logging.INFO, show_mod_func=False)

    # Check for trial directories and their content
    trial_dirs = sys.argv[1:]
    if not trial_dirs or not trial_yaml_files_exist(trial_dirs):
        logging.fatal('usage: verde.py [trial_dirs] # NB: A trial.yaml file must exist in each dir.')
        exit(1)

    # Run trials
    for trial_dir in trial_dirs:
        run_trial(trial_dir)
