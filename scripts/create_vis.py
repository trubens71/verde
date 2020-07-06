import verde.verde_common as vc

input_data_file = '../asc_data/processed/set_00/AFR_T1_ASCOF_1A.csv'
cql_query_file = '../trials/AFR_T1_ASCOF_1A.cql.json'
verde_rule_file = '../trials/AFR_T1_ASCOF_1A_rule1_v2.lp'
trial_output_prefix = '../trials/AFR_T1_ASCOF_1A'

if __name__ == "__main__":
    logging = vc.configure_logger('verde_run.log')
    csv_file, col_dict = vc.fix_csv_column_headers(input_data_file)
    schema_file, schema_asp = vc.create_schema_asp(csv_file)
    query_file, query_asp = vc.create_cql_query_asp(cql_query_file)
    verde_rule_asp = vc.create_verde_rule_asp(verde_rule_file)
    vc.run_trial([schema_asp, query_asp], trial_output_prefix, '01')
    vc.run_trial([schema_asp, query_asp, verde_rule_asp], trial_output_prefix, '02')

