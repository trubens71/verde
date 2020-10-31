"""
Main script to execute a verde trial based on config files trial.yaml in specified directories.
"""

import sys
import src.utils as vutils
from src.trial import Trial
import logging

if __name__ == "__main__":

    """
    Run trials based on a list of trial directories passed on the command line.
    Each directory must have a trial.yaml file in it.
    """

    logging = vutils.configure_logger('verde.log', logging.INFO, show_mod_func=False)
    trial_dirs = sys.argv[1:]  # get command line arguments

    # Check we were passed some arguments
    if not trial_dirs:
        logging.fatal('usage: verde.py [trial_dirs] \t# a trial.yaml file must exist in each trial_dir.')
        exit(1)

    # instantiate the trials based on directories passed as arguments,
    # this validates all trials before we run any of them.
    trials = []
    for trial_dir in trial_dirs:
        trials.append(Trial(trial_dir))

    # Run the trials and their experiments
    experiments_ran = []
    for trial in trials:
        logging.info(f'*** running trial {trial.trial_id} ***')
        for exp in trial.experiments:
            if exp.do:
                exp.run()
                experiments_ran.append(exp.id)
            else:
                logging.warning(f'{exp.experiment_id} is disabled in config')
        trial.exec_regression_test()

    logging.info(f'Completed experiments {experiments_ran}')
