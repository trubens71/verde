import logging
import json
from shapely.geometry import LineString
import os
import pandas as pd
import altair as alt


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
                            'crossed': 'not'})

    # some summary stats
    b_not_in_v = [baseline_results[i]['matches'] for i,_ in enumerate(baseline_results) ].count(None)
    v_not_in_b = [verde_results[i]['matches'] for i,_ in enumerate(verde_results) ].count(None)
    logging.info(f'{len(matches)} matching visualisations between baseline and verde '
                 f'{len(matches)/len(baseline_results):.1%}')
    logging.info(f'{b_not_in_v} baseline visualisations not in verde')
    logging.info(f'{v_not_in_b} verde visualisations not in verde')

    # identify crossed edges which signifies a different ranking between baseline and verde
    # inspect the matches pairwise and tag them if they intersect.
    match_idx_pairs = [(m, n) for m, _ in enumerate(matches) for n, _ in enumerate(matches) if m < n]
    for m, n in match_idx_pairs:
        line_m = LineString([(0, matches[m]['b_rank']), (1, matches[m]['v_rank'])])
        line_n = LineString([(0, matches[n]['b_rank']), (1, matches[n]['v_rank'])])
        if line_m.intersects(line_n):
            for i in [m, n]:
                if matches[i]['b_cost'] == matches[i]['v_cost']:
                    matches[i]['crossed'] = 'with_equal_cost'
                else:
                    matches[i]['crossed'] = 'with_diff_cost'

    # write the match file to csv for exploratory visualisation
    df = pd.DataFrame(matches)
    df['match'] = df.index
    df = df.melt(id_vars=['match', 'crossed', 'b_cost', 'v_cost'], var_name='set', value_name='rank')
    df.set = df.set.str.replace('b_rank', 'baseline')
    df.set = df.set.str.replace('v_rank', 'verde')
    match_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_compare_match.csv')
    logging.info(f'writing comparison matches to {match_csv_file}')
    df.to_csv(match_csv_file, index=False)

    # simplify and union the visualisation model data
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

    create_exploratory_visualisation(trial_id, directory, vis_csv_file, match_csv_file)
    write_single_vis_viewer(trial_id, directory)


def find_crossed_matches(matches):
    for i, _ in enumerate(matches):
        matches[i]['crossed'] = False

    match_idx_pairs = [(m, n) for m, _ in enumerate(matches) \
                       for n, _ in enumerate(matches) if m < n]

    for m, n in match_idx_pairs:
        if (matches[n]['a_rank'] > matches[m]['a_rank'] and matches[n]['b_rank'] < matches[m]['b_rank']) or \
                (matches[n]['a_rank'] < matches[m]['a_rank']
                 and matches[n]['b_rank'] > matches[m]['b_rank']):
            matches[m]['crossed'] = True
            matches[n]['crossed'] = True

    return matches


def write_single_vis_viewer(trial_id, directory):

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
        <!-- Import Vega & Vega-Lite (does not have to be from CDN) -->
        <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
        <!-- Import vega-embed -->
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
    </head>
    <body>
    
    <script>
        var url_string = window.location.href
        var url = new URL(url_string);
        var vl_json = url.searchParams.get("vl_json");
        //console.log(c);
    </script>
    
    <div id="vis"></div>
    <script type="text/javascript">
        var spec = vl_json;
        vegaEmbed('#vis', spec).then(function(result) {}).catch(console.error);
    </script>
    
    </body>
    </html>    
    """

    with open(os.path.join(directory, 'vegalite', f'{trial_id}_view_one_vl.html'), 'w') as f:
        f.write(html)


def create_exploratory_visualisation(trial_id, directory, vis_data_file, match_data_file):

    vl_viewer = f'{trial_id}_view_one_vl.html?vl_json='

    # first layer is just two columns of square marks
    chart = alt.Chart(os.path.basename(vis_data_file)).mark_square(
        size=100
    ).transform_calculate(
        rank="format(datum.rank,'03')",
        has_match="toBoolean(datum.matches)",
        link=f"'{vl_viewer}' + datum.vl_spec_file"
    ).encode(
        alt.X(
            'set:O',
            axis=alt.Axis(labelAngle=0)
        ),
        alt.Y(
            'rank:O'
        ),
        tooltip=['rank:N', 'cost:Q', 'props:N', 'violations:N', 'vl:N'],
        opacity=alt.Opacity('has_match:O', legend=None),
        href="link:N"
    ).properties(
        width=250
    )

    # second layer is match lines

    col_domain = ['not', 'with_equal_cost', 'with_diff_cost']
    col_range_ = ['steelblue', 'green', 'red']

    chart += alt.Chart(os.path.basename(match_data_file)).mark_line().transform_calculate(
        rank="format(datum.rank,'03')"
    ).encode(
        alt.X(
            'set:O'
        ),
        alt.Y(
            'rank:O'
        ),
        detail='match:N',
        color=alt.Color('crossed:N', scale=alt.Scale(domain=col_domain, range=col_range_))
    )

    chart.save(os.path.join(directory, 'vegalite', f'{trial_id}_compare.html'))


create_exploratory_visualisation('trial_01.exp_01',
                                 '../laboratory/trial_01',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_compare_vis.csv',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_compare_match.csv')