view(v_v).
num_rows(63).

fieldtype("Region_code",string).
cardinality("Region_code", 9).
fieldtype("Region_name",string).
cardinality("Region_name", 9).
fieldtype("Setting",string).
cardinality("Setting", 7).
fieldtype("Gross_Current_Expenditure_x1000",number).
cardinality("Gross_Current_Expenditure_x1000", 63).
fieldtype("Gross_Current_Expenditure_Proportion",number).
cardinality("Gross_Current_Expenditure_Proportion", 63).

encoding(v_v,e0).
encoding(v_v,e1).
:- not field(v_v,E,"Setting") : encoding(v_v,E).
:- not field(v_v,E,"Gross_Current_Expenditure_x1000") : encoding(v_v,E).
