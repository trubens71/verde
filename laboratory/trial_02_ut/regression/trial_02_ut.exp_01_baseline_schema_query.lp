view(v_v).
num_rows(151).

fieldtype("Geography_code",string).
cardinality("Geography_code", 151).
fieldtype("LA_code",number).
cardinality("LA_code", 151).
fieldtype("LA_name",string).
cardinality("LA_name", 151).
fieldtype("Region_code",string).
cardinality("Region_code", 9).
fieldtype("Region_name",string).
cardinality("Region_name", 9).
fieldtype("Net_Total_Expenditure_x1000",number).
cardinality("Net_Total_Expenditure_x1000", 151).
fieldtype("Gross_Total_Expenditure_x1000",number).
cardinality("Gross_Total_Expenditure_x1000", 151).
fieldtype("Gross_Current_Expenditure_x1000",number).
cardinality("Gross_Current_Expenditure_x1000", 151).
fieldtype("Number_of_requests_for_support_received_from_new_clients_18_to_64",number).
cardinality("Number_of_requests_for_support_received_from_new_clients_18_to_64", 148).
fieldtype("Number_of_requests_for_support_received_from_new_clients_65_and_over",number).
cardinality("Number_of_requests_for_support_received_from_new_clients_65_and_over", 147).
fieldtype("New_clients_with_an_episode_of_ST_Max_care_and_a_known_sequel_18_to_64",number).
cardinality("New_clients_with_an_episode_of_ST_Max_care_and_a_known_sequel_18_to_64", 66).
fieldtype("New_clients_with_an_episode_of_ST_Max_care_and_a_known_sequel_65_and_over",number).
cardinality("New_clients_with_an_episode_of_ST_Max_care_and_a_known_sequel_65_and_over", 126).
fieldtype("Long_Term_Support_during_the_year_18_to_64",number).
cardinality("Long_Term_Support_during_the_year_18_to_64", 135).
fieldtype("Long_Term_Support_during_the_year_65_and_over",number).
cardinality("Long_Term_Support_during_the_year_65_and_over", 141).
fieldtype("Support_provided_to_carers_during_the_year",number).
cardinality("Support_provided_to_carers_during_the_year", 145).
fieldtype("Social_care_related_quality_of_life_score_All",number).
cardinality("Social_care_related_quality_of_life_score_All", 25).
fieldtype("Social_care_related_quality_of_life_score_Male",number).
cardinality("Social_care_related_quality_of_life_score_Male", 27).
fieldtype("Social_care_related_quality_of_life_score_Female",number).
cardinality("Social_care_related_quality_of_life_score_Female", 27).
fieldtype("Social_care_related_quality_of_life_score_18_to_64",number).
cardinality("Social_care_related_quality_of_life_score_18_to_64", 29).
fieldtype("Social_care_related_quality_of_life_score_65_and_over",number).
cardinality("Social_care_related_quality_of_life_score_65_and_over", 27).

encoding(v_v,e0).
encoding(v_v,e1).
encoding(v_v,e2).
:- not field(v_v,E,"Social_care_related_quality_of_life_score_All") : encoding(v_v,E).
:- field(v_v,E,"Social_care_related_quality_of_life_score_All"), not zero(v_v,E).
:- not field(v_v,E,"Gross_Total_Expenditure_x1000") : encoding(v_v,E).
:- field(v_v,E,"Gross_Total_Expenditure_x1000"), not log(v_v,E).
:- not field(v_v,E,"Support_provided_to_carers_during_the_year") : encoding(v_v,E).
:- field(v_v,E,"Support_provided_to_carers_during_the_year"), not zero(v_v,E).
