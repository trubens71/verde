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

% --- verde rule04 (colour schemes and mark colours) *** --------------------------------------------------------------%

% field to colour properties (facts)
fieldmarkcolor("Geography_code","{\"color\": \"slategray\"}",1).
fieldmarkcolor("LA_code","{\"color\": \"slategray\"}",1).
fieldmarkcolor("LA_name","{\"color\": \"gray\"}",0).
fieldmarkcolor("Region_code","{\"color\": \"slategray\"}",1).
fieldmarkcolor("Region_name","{\"color\": \"black\"}",0).

fieldcolorscheme("Net_Total_Expenditure_x1000", "{\"scheme\": \"oranges\"}",0).
fieldcolorscheme("Gross_Total_Expenditure_x1000", "{\"scheme\": \"oranges\"}",0).
fieldcolorscheme("Gross_Current_Expenditure_x1000", "{\"scheme\": \"oranges\"}",0).
fieldcolorscheme("Social_care_related_quality_of_life_score_All", "{\"scheme\": \"greens\"}",1).
fieldcolorscheme("Social_care_related_quality_of_life_score_Male", "{\"scheme\": \"greens\"}",1).
fieldcolorscheme("Social_care_related_quality_of_life_score_Female", "{\"scheme\": \"greens\"}",1).
fieldcolorscheme("Social_care_related_quality_of_life_score_18_to_64", "{\"scheme\": \"greens\"}",1).
fieldcolorscheme("Social_care_related_quality_of_life_score_65_and_over", "{\"scheme\": \"greens\"}",1).

% rule definitions

%----------------------------------------------------------------------------------------------------------------------%
% first case: color channel is used and we have a scheme for the encoding field.
verde_color_enc_scheme_choices(V,E,F,T,CS,D) :- fieldcolorscheme(F,CS,D), field(V,E,F), type(V,E,T), channel(V,E,color).

% choose only one with minimum distance from domain node with scheme to the mapped node
1 { verde_color_enc_scheme(V,E,F,T,CS,D) } 1 :- verde_color_enc_scheme_choices(V,E,F,T,CS,D),
                                                #min { DD : verde_color_enc_scheme_choices(_,_,_,_,_,DD) } = D.

%----------------------------------------------------------------------------------------------------------------------%
% second case: if first case not applied, and we have non-aggregated field encoding for which there is a schema,
% then we will double encode that field.
verde_color_double_enc_scheme_choices(V,E,F,T,CS,D) :- not channel(_,_,color),
                                                       not verde_color_enc_scheme(_,_,_,_,_,_),
                                                       field(V,E,F), type(V,E,T),
                                                       not aggregate(V,E,_),
                                                       discrete(V,E), fieldcolorscheme(F,CS,D).
% choose only one
1 { verde_color_double_enc_scheme(V,E,F,T,CS,D) } 1 :- verde_color_double_enc_scheme_choices(V,E,F,T,CS,D),
                                                       #min { DD : verde_color_double_enc_scheme_choices(_,_,_,_,_,DD) }
                                                         = D.

%----------------------------------------------------------------------------------------------------------------------%
% third case: if first two cases does not apply but we have an appropriate mark color
verde_mark_color_choices(V,CO,D) :- not channel(_,_,color),
                                    not verde_color_enc_scheme(_,_,_,_,_,_),
                                    not verde_color_double_enc_scheme(_,_,_,_,_,_),
                                    view(V), fieldmarkcolor(F,CO,D),
                                    fieldtype(F,FT), FT != "number",
                                    cardinality(F,CA), num_rows(NR), CA = NR.

% choose only one mark colour with minimum distance between node with mark colour and mapped node
1 { verde_color_mark(V,CO,D) } 1 :- verde_mark_color_choices(V,CO,D),
                                    #min { DD : verde_mark_color_choices(_,_,DD) } = D.

%----------------------------------------------------------------------------------------------------------------------%

% outputs for translation to vl spec properties
#show verde_color_enc_scheme/6.
#show verde_color_double_enc_scheme/6.
#show verde_color_mark/3.

% set these as zero weight soft rules, helps in the comparative analysis v baseline
soft(verde_color_enc_scheme,V,E) :- verde_color_enc_scheme(V,E,F,T,CS,D).
soft(verde_color_double_enc_scheme,V,E) :- verde_color_double_enc_scheme(V,E,F,T,CS,D).
soft(verde_color_mark,V,CO) :- verde_color_mark(V,CO,D).

#const verde_color_enc_scheme_weight = 0.
#const verde_color_double_enc_scheme_weight = 0.
#const verde_color_mark_weight = 0.

soft_weight(verde_color_enc_scheme, verde_color_enc_scheme_weight).
soft_weight(verde_color_double_enc_scheme, verde_color_double_enc_scheme_weight).
soft_weight(verde_color_mark, verde_color_mark_weight).

% *** end of verde rule 04 lp *** -------------------------------------------------------------------------------------%
