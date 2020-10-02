import sys
import src.utils as vu
from src.trial import Trial
import logging
import os

TRIAL_YAML = 'trial.yaml'


def run_trial(directory):
    experiments_ran = []
    trial = Trial(directory, TRIAL_YAML)
    for exp in trial.experiments:
        if exp.do:
            exp.run()
            experiments_ran.append(exp.id)
        else:
            logging.warning(f'{exp.experiment_id} is disabled in config')
    logging.info(f'Completed running {experiments_ran}')


def trial_yaml_files_exist(dirs):
    """
    Make sure all dirs from command line exist and have a trial.yaml file.
    :param dirs: list of directories
    :return: config_ok boolean
    """

    config_ok = True

    for d in dirs:
        if not os.path.isdir(d):
            logging.fatal(f'directory {d} not found')
            config_ok = False
        elif not os.path.isfile(f'{d}/{TRIAL_YAML}'):
            logging.fatal(f'no {TRIAL_YAML} found in {d}')
            config_ok = False

    return config_ok


if __name__ == "__main__":

    logging = vu.configure_logger('verde.log', logging.INFO, show_mod_func=False)
    # Check for trial directories and their content
    trial_dirs = sys.argv[1:]
    if not trial_dirs or not trial_yaml_files_exist(trial_dirs):
        logging.fatal('usage: verde.py [trial_dirs] # NB: A trial.yaml file must exist in each dir.')
        exit(1)
    # Run trials
    for trial_dir in trial_dirs:
        run_trial(trial_dir)
