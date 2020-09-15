import logging
import src.utils as vutils
import src.draco_proxy as vdraco
import src.domain_rules as vrules
import src.vis_results as vresults


class Experiment:

    def __init__(self, trial, exp):
        """
        Construct an experiment
        :param trial: the parent trial object from which we inherit some values
        :param exp: the config details for this experiment
        """

        self.verde_meta_schema = None
        self.domain_schema = None
        self.domain_mapping_schema = None
        self.input_data_file = None
        self.input_mapping_file = None
        self.query = None
        self.query_enc_fields = None
        self.execute = None
        self.baseline_schema_query_lp = None
        self.verde_schema_query_lp = None
        self.draco_base_lp_dir = None
        self.baseline_vis_results = None
        self.baseline_vis_results_json = None
        self.num_models = None
        self.verde_vis_results = None
        self.verde_vis_results_json = None
        self.verde_base_lp_override_dir = None

        # create a composite id of trial and experiment
        self.id = f"{trial.trial_id}.{exp['experiment_id']}"
        logging.info(f'creating experiment {self.id}')

        # inherit some values from the trial for easier future referencing
        self.trial_id = trial.trial_id
        self.trial_desc = trial.trial_desc
        self.directory = trial.directory

        # copy the experiment config into the class
        for k, v in exp.items():
            setattr(self, k, v)

        # override with any duplicated values from the trial
        for trial_k, trial_v in trial.global_config.items():
            if hasattr(self, trial_k) and getattr(self, trial_k) is not None:
                logging.warning(f"global config {trial_k}={trial_v} overriding {getattr(self, trial_k)} in {self.id}")
            setattr(self, trial_k, trial_v)

    def run(self):
        """
        Run the experiment
        :return: None
        """

        logging.info(f'running experiment {self.id}')

        # clear out temp files from previous runs based on id and directory
        vutils.delete_temp_files(self.directory, self.id)

        # validate the domain schema against the verde meta schema
        if self.execute.validate_domain_schema.do:
            if not vutils.validate_json_doc(self.domain_schema, self.verde_meta_schema):
                exit(1)
        else:
            logging.warning('validate_domain_schema json validation turned off in trial config')

        # validate the input mapping file against the domain schema.
        # note that this involves $refs to the domain model so needs the domain model to be publicly available on github
        if self.execute.validate_input_file_mapping.do:
            if not vutils.validate_json_doc(self.input_mapping_file, self.domain_mapping_schema):
                exit(1)
        else:
            logging.warning('validate_input_file_mapping json validation turned off in trial config')

        # Clingo does not like spaces and special chars in atom names so we need to fix the input csv file
        # and the file that maps it to the domain model.
        if self.execute.fix_input_file_column_names.do:
            self.input_data_file, self.input_mapping_file, self.query = \
                vutils.fix_column_headings(self.input_data_file, self.input_mapping_file, self.id, self.query,
                                           self.directory + '/data', )
        else:
            logging.warning('fix_input_file_column_names turned off in trial config')

        if self.execute.create_baseline_schema_query_lp.do:
            self.baseline_schema_query_lp, self.query_enc_fields = \
                vdraco.get_baseline_schema_query_lp(self.input_data_file,
                                                    self.query,
                                                    self.id,
                                                    self.directory,
                                                    self.execute.create_baseline_schema_query_lp.write_lp)
        else:
            logging.warning('create_baseline_schema_query_lp turned off in trial config')

        if self.execute.create_verde_rules_lp.do:
            self.verde_schema_query_lp = vrules.create_verde_rules_lp(self.domain_schema,
                                                                      self.input_mapping_file,
                                                                      self.query_enc_fields,
                                                                      self.id,
                                                                      self.directory,
                                                                      self.execute.create_verde_rules_lp,
                                                                      self.baseline_schema_query_lp)
        else:
            logging.warning('create_verde_rules_lp turned off in trial config')

        if self.execute.get_baseline_visualisations.do and self.baseline_schema_query_lp:
            self.baseline_vis_results, self.baseline_vis_results_json = \
                vresults.get_vis_results(self.id, self.directory, self.input_data_file,
                                         self.baseline_schema_query_lp,
                                         self.draco_base_lp_dir,
                                         num_models=self.num_models,
                                         label='baseline')
        else:
            logging.warning(f'cannot get baseline visualisations due to trial config conflict')

        if self.execute.get_verde_visualisations.do and self.verde_schema_query_lp:
            self.verde_vis_results, self.verde_vis_results_json = \
                vresults.get_vis_results(self.id, self.directory, self.input_data_file,
                                         self.verde_schema_query_lp,
                                         self.draco_base_lp_dir,
                                         override_lp_dir=self.verde_base_lp_override_dir,
                                         num_models=self.num_models,
                                         label='verde')
        else:
            logging.warning(f'cannot get verde visualisations due to trial config conflict')

