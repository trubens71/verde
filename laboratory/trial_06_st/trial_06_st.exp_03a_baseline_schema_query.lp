view(v_v).
num_rows(20).

fieldtype("region",string).
cardinality("region", 10).
fieldtype("region_code",string).
cardinality("region_code", 10).
fieldtype("gender",string).
cardinality("gender", 2).
fieldtype("QoL",number).
cardinality("QoL", 11).

encoding(v_v,e0).
encoding(v_v,e1).
encoding(v_v,e2).
:- not field(v_v,E,"region") : encoding(v_v,E).
:- not field(v_v,E,"gender") : encoding(v_v,E).
:- not field(v_v,E,"QoL") : encoding(v_v,E).
:- field(v_v,E,"QoL"), not not zero(v_v,E).
