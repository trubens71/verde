% Logic program for AFR_T1_ASCOF_1A test case, to state preference
% for expenditure to be on x-axis and quality of life on y-axis.
%
% Facts from main test case lp:
%   encoding(e0).
%   field(e0,"Social_care_related_quality_of_life_score_All").
%   encoding(e1).
%   field(e1,"Gross_Total_Expenditure_x1000").
%-----------------------------------------------------------------
% Soft constraints (preferences)

% @constraint prefer expenditure to be on x-axis and quality of life on y.
soft(e0_x) :- channel(e0,x), not channel(e0,y).
% @constraint complement to above.
soft(e1_y) :- channel(e1,y), not channel(e1,x).

%-----------------------------------------------------------------
% Weights - just enough to nudge the binary choice the right way.
#const e0_x_weight = 1.
#const e1_y_weight = 1.

%-----------------------------------------------------------------
% Assign weights
soft_weight(e0_x,e0_x_weight).
soft_weight(e1_y,e1_y_weight).
