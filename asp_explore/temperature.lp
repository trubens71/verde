% From University of Texas guide

t(austin,88). t(dallas,95). t(houston,90). t(san_antonio,85).

warm(C) :- t(C,T1), t(austin,T2), T1>T2.

#show warm/1.