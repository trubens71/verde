view(v_v).
num_rows(10).

fieldtype("region",string).
cardinality("region", 10).
fieldtype("region_code",string).
cardinality("region_code", 10).
fieldtype("zero_hr_contract_all_pct",number).
cardinality("zero_hr_contract_all_pct", 10).
fieldtype("zero_hr_contract_managerial_pct",number).
cardinality("zero_hr_contract_managerial_pct", 9).
fieldtype("zero_hr_contract_reg_prof_pct",number).
cardinality("zero_hr_contract_reg_prof_pct", 8).
fieldtype("zero_hr_contract_direct_care_pct",number).
cardinality("zero_hr_contract_direct_care_pct", 10).
fieldtype("zero_hr_contract_other_pct",number).
cardinality("zero_hr_contract_other_pct", 9).
fieldtype("vacancies_all_pct",number).
cardinality("vacancies_all_pct", 9).
fieldtype("vacancies_managerial_pct",number).
cardinality("vacancies_managerial_pct", 8).
fieldtype("vacancies_reg_prof_pct",number).
cardinality("vacancies_reg_prof_pct", 10).
fieldtype("vacancies_direct_care_pct",number).
cardinality("vacancies_direct_care_pct", 9).
fieldtype("vacancies_other_pct",number).
cardinality("vacancies_other_pct", 8).
fieldtype("QoL_all",number).
cardinality("QoL_all", 4).
fieldtype("QoL_male",number).
cardinality("QoL_male", 7).
fieldtype("QoL_female",number).
cardinality("QoL_female", 7).
fieldtype("QoL_18_64",number).
cardinality("QoL_18_64", 6).
fieldtype("QoL_65_over",number).
cardinality("QoL_65_over", 5).

encoding(v_v,e0).
encoding(v_v,e1).
:- not field(v_v,E,"region") : encoding(v_v,E).
:- not field(v_v,E,"zero_hr_contract_all_pct") : encoding(v_v,E).
:- field(v_v,E,"zero_hr_contract_all_pct"), not zero(v_v,E).
