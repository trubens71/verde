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

% --- verde rule 03 (sort order for ordinals) -------------------------------------------------------------------------%

% these facts state the association of a sort order to the field

fieldcustomsortorder("Setting","['Community: Supported Living', 'Community: Direct Payments', 'Community: Other Long Term Care', 'Community: Home Care', 'Supported Accommodation', 'Residential', 'Nursing']").


%----------------------------------------------------------------------------------------------------------------------%

% this rule determines that a custom order exists provided the
% resulting draco encoding is nominal or ordinal.

verde_ordinal_sort(V,E,C,F,O) :- fieldcustomsortorder(F,O),
                                 field(V,E,F), type(V,E,(nominal;ordinal)),
                                 channel(V,E,C).

%----------------------------------------------------------------------------------------------------------------------%

% outputs for translation to vl spec properties

#show verde_ordinal_sort/5.

% set this as zero weight soft rules, helps in the comparative analysis v baseline

soft(verde_ordinal_sort,V,E):- verde_ordinal_sort(V,E,C,F,O).
#const verde_ordinal_sort_weight = 0.
soft_weight(verde_ordinal_sort, verde_ordinal_sort_weight).

% *** end of verde rule 03 lp *** -------------------------------------------------------------------------------------%
