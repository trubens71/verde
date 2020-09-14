import verde_old.verde_utils as vu
import src.domain_rules as vr
import logging

domain_schema_file = '../schemas/verde_asc_domain_schema.json'

input_data_file = '../asc_data/processed/set_00/AFR_T1_ASCOF_1A.csv'
input_mapping_file = '../asc_data/processed/set_00/AFR_T1_ASCOF_1A_mapping.json'

cql_query_file = '../trials/AFR_T1_ASCOF_1A_b.cql.json'
verde_rule_file = '../trials/AFR_T1_ASCOF_1A_rule1_v3.lp'
trial_output_prefix = '../trials/AFR_T1_ASCOF_1A_b'


if __name__ == "__main__":
    logging = vu.configure_logger('create_vis.log', logging.DEBUG)
    csv_file, col_dict = vu.fix_csv_column_headers(input_data_file)
    schema_file, schema_asp = vu.create_schema_asp(csv_file)
    query_file, query_asp = vu.create_cql_query_asp(cql_query_file)
    verde_rule_asp = vr.create_verde_rule_asp(query_asp, domain_schema_file, input_mapping_file)
    vu.run_trial([schema_asp, query_asp], trial_output_prefix, '01')
    vu.run_trial([schema_asp, query_asp, verde_rule_asp], trial_output_prefix, '02')
    pass

