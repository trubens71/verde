import logging
import json
from shapely.geometry import LineString
import os
import pandas as pd


def compare_baseline_to_verde(trial_id, directory, baseline_results, verde_results):
    """
    Identify the differences between the baseline vis set and the verde vis set:
    - Vis specs present in one set but not the other
    - Identical Vis specs but with different rankings or different costs
    Go on to produce an exploratory visualisation to present the comparison.
    :param trial_id:
    :param directory:
    :param baseline_results:
    :param verde_results:
    :return:
    """

    # will later augment our results with cross reference of matches between sets, so initialise all as None
    for result_set in [baseline_results, verde_results]:
        for result in result_set:
            result['matches'] = None

    # conduct a pairwise comparison of specs in each set.
    b_v_pairs = [(b, v) for b, _ in enumerate(baseline_results) for v, _ in enumerate(verde_results)]
    matches = []
    for b, v in b_v_pairs:
        # remove the title before comparing the guts of the vl spec
        b_cmp = baseline_results[b]['vl']
        b_cmp.pop('title', None)
        v_cmp = verde_results[v]['vl']
        v_cmp.pop('title', None)
        if b_cmp == v_cmp:
            baseline_results[b]['matches'] = v
            verde_results[v]['matches'] = b
            matches.append({'b_rank': b,
                            'b_cost': baseline_results[b]['cost'],
                            'v_rank': v,
                            'v_cost': verde_results[v]['cost'],
                            'overlap': None})

    # some summary stats
    b_not_in_v = [baseline_results[i]['matches'] for i,_ in enumerate(baseline_results) ].count(None)
    v_not_in_b = [verde_results[i]['matches'] for i,_ in enumerate(verde_results) ].count(None)
    logging.info(f'{len(matches)} matching visualisations between baseline and verde '
                 f'{len(matches)/len(baseline_results):.1%}')
    logging.info(f'{b_not_in_v} baseline visualisations not in verde')
    logging.info(f'{v_not_in_b} verde visualisations not in verde')

    # identify overlapping edges which signifies a different ranking between baseline and verde
    # inspect the matches pairwise and tag them if they intersect.
    match_idx_pairs = [(m, n) for m, _ in enumerate(matches) for n, _ in enumerate(matches) if m < n]
    for m, n in match_idx_pairs:
        line_m = LineString([(0, matches[m]['b_rank']), (1, matches[m]['v_rank'])])
        line_n = LineString([(0, matches[n]['b_rank']), (1, matches[n]['v_rank'])])
        if line_m.intersects(line_n):
            for i in [m, n]:
                if matches[i]['b_cost'] == matches[i]['v_cost']:
                    matches[i]['overlap'] = 'equal_cost'
                else:
                    matches[i]['overlap'] = 'diff_cost'

    # write the match file to csv for exploratory visualisation
    df = pd.DataFrame(matches)
    match_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_compare_match.csv')
    logging.info(f'writing comparison matches to {match_csv_file}')
    df.to_csv(match_csv_file, index=False)

    # simplify and union the visualisation data
    df_baseline = pd.DataFrame(baseline_results)
    df_baseline['set'] = 'baseline'
    df_baseline['rank'] = df_baseline.index
    df_verde = pd.DataFrame(verde_results)
    df_verde['set'] = 'verde'
    df_verde['rank'] = df_verde.index
    df = pd.concat([df_baseline, df_verde])
    df.vl_spec_file = df.vl_spec_file.apply(lambda x: os.path.basename(x))
    vis_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_compare_vis.csv')
    logging.info(f'writing comparison nodes to {vis_csv_file}')
    df.to_csv(vis_csv_file, index=False)