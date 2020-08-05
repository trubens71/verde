  % From University of Texas guide

% rule...
warm(C) :- t(C,T1), t(austin,T2), T1>T2.
% head :- body
% :- reads 'if'
% variables C, T1, T2 are capitalised
% austin not capitalised as is an object not a variable
% variables and object names are 'terms'. There are other kinds of terms.
% predicate symbols like 'warm' and t denote properties and relationships
% A predicate symbols and its terms make an atom.
% T1>T2 is a comparion
% Typically head of a rule is an atom, body is a list of atoms and comparisons.
% Supported comparions are = != < > <= >=
% Rule says: C is warm if temp in C is T1 and temp in austin is T2 and T1>T2


t(c,88). t(dallas,95). t(houston,90). t(san_antonio,85).
% These are facts. No if, no body. No variables so are 'ground'
#const c=austin. % c is a placeholder

#show warm/1.
% show atoms of predicate symbol warm with one argument
