view(v_v).
num_rows(18).

fieldtype("Region_code",string).
cardinality("Region_code", 9).
fieldtype("Region_name",string).
cardinality("Region_name", 9).
fieldtype("Age_Group",string).
cardinality("Age_Group", 2).
fieldtype("New_Client_Requests",number).
cardinality("New_Client_Requests", 18).
fieldtype("ST_Max_Care",number).
cardinality("ST_Max_Care", 18).
fieldtype("Long_Term_Care",number).
cardinality("Long_Term_Care", 18).

encoding(v_v,e0).
encoding(v_v,e1).
encoding(v_v,e2).
:- not field(v_v,E,"New_Client_Requests") : encoding(v_v,E).
:- field(v_v,E,"New_Client_Requests"), not zero(v_v,E).
:- not field(v_v,E,"ST_Max_Care") : encoding(v_v,E).
:- field(v_v,E,"ST_Max_Care"), not zero(v_v,E).
:- not field(v_v,E,"Age_Group") : encoding(v_v,E).
