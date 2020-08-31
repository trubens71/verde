import sys
import src.verde_utils as vu
import src.trial as vt
import logging
import os

TRIAL_YAML = 'trial.yaml'


def run_trial(directory):
    trial = vt.Trial(directory, TRIAL_YAML)
    for exp in trial.experiments:
        logging.debug(exp['id'])
    pass


def trial_yaml_exist(dirs):
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

    logging = vu.configure_logger('verde.log', logging.DEBUG)

    # Check for trial directories and their content
    trial_dirs = sys.argv[1:]
    if not trial_dirs or not trial_yaml_exist(trial_dirs):
        logging.fatal('usage: verde.py [trial_dirs] # NB: A trial.yaml file must exist in each dir.')
        exit(1)

    # Run trials
    for trial_dir in trial_dirs:
        run_trial(trial_dir)
