import verde.verde_utils as vu

input_data_file = '../asc_data/processed/set_00/AFR_T1_ASCOF_1A.csv'
cql_query_file = '../trials/AFR_T1_ASCOF_1A.cql.json'
verde_rule_file = '../trials/AFR_T1_ASCOF_1A_rule1_v2.lp'
trial_output_prefix = '../trials/AFR_T1_ASCOF_1A'

if __name__ == "__main__":
    logging = vu.configure_logger('create_vis.log')
    csv_file, col_dict = vu.fix_csv_column_headers(input_data_file)
    schema_file, schema_asp = vu.create_schema_asp(csv_file)
    query_file, query_asp = vu.create_cql_query_asp(cql_query_file)
    verde_rule_asp = vu.create_verde_rule_asp(verde_rule_file)
    vu.run_trial([schema_asp, query_asp], trial_output_prefix, '01')
    vu.run_trial([schema_asp, query_asp, verde_rule_asp], trial_output_prefix, '02')

