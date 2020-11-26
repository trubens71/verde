view(v_v).
num_rows(40).

fieldtype("region",string).
cardinality("region", 10).
fieldtype("region_code",string).
cardinality("region_code", 10).
fieldtype("role",string).
cardinality("role", 4).
fieldtype("vacancies_pct",number).
cardinality("vacancies_pct", 33).
fieldtype("zero_hr_contract_pct",number).
cardinality("zero_hr_contract_pct", 35).

encoding(v_v,e0).
encoding(v_v,e1).
encoding(v_v,e2).
:- not field(v_v,E,"region") : encoding(v_v,E).
:- not field(v_v,E,"role") : encoding(v_v,E).
:- not field(v_v,E,"zero_hr_contract_pct") : encoding(v_v,E).
:- field(v_v,E,"zero_hr_contract_pct"), not zero(v_v,E).
