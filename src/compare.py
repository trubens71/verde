import logging
from shapely.geometry import LineString
import os
import pandas as pd
import altair as alt
from altair import datum


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
                    matches[i]['crossed'] = 'with_different_cost'

    # write the match file to csv for exploratory visualisation
    df = pd.DataFrame(matches)
    df['match'] = df.index
    df = df.melt(id_vars=['match', 'crossed', 'b_cost', 'v_cost'], var_name='set', value_name='rank')
    df.set = df.set.str.replace('b_rank', 'baseline')
    df.set = df.set.str.replace('v_rank', 'verde')
    match_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_match.csv')
    logging.info(f'writing comparison matches to {match_csv_file}')
    df.to_csv(match_csv_file, index=False)

    # simplify and union the visualisation model (instance) data
    df_baseline = pd.DataFrame(baseline_results)
    df_baseline['set'] = 'baseline'
    df_baseline['rank'] = df_baseline.index
    df_verde = pd.DataFrame(verde_results)
    df_verde['set'] = 'verde'
    df_verde['rank'] = df_verde.index
    df = pd.concat([df_baseline, df_verde])
    df['has_match'] = df.matches.notnull()
    df.vl_spec_file = df.vl_spec_file.apply(lambda x: os.path.basename(x))
    vis_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_model.csv')
    logging.info(f'writing comparison models to {vis_csv_file}')
    df.to_csv(vis_csv_file, index=False)

    # create violation data for the exploratory vis
    violation_records = []
    for _, row in df.iterrows():
        violations = dict(row.violations)
        for violation in violations.keys():
            record = violations[violation]
            record['violation'] = violation
            record['set'] = row['set']
            record['rank'] = row['rank']
            violation_records.append(record)
    df_violations = pd.DataFrame(violation_records)
    df_violations = df_violations[['set', 'rank', 'violation', 'num', 'weight', 'cost_contrib']]
    violations_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_violations.csv')
    logging.info(f'writing comparison violations to {violations_csv_file}')
    df_violations.to_csv(violations_csv_file, index=False)

    # create prop data for the exploratory vis
    prop_records = []
    for _, row in df.iterrows():
        for prop in row.props:
            record = {'set': row['set'], 'rank': row['rank'], 'prop': prop}
            prop_records.append(record)
    df_props = pd.DataFrame(prop_records)
    props_csv_file = os.path.join(directory, 'vegalite', f'{trial_id}_view_compare_props.csv')
    logging.info(f'writing comparison props to {props_csv_file}')
    df_props.to_csv(props_csv_file, index=False)

    # produce the exploratory vis and a viewer to support hyperlink click through
    create_exploratory_visualisation(trial_id, directory, vis_csv_file, match_csv_file,
                                     violations_csv_file, props_csv_file)
    # A generic html file to present a single vl spec passed as a parameter
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


def create_exploratory_visualisation(trial_id, directory, vis_data_file, match_data_file,
                                     violations_data_file, props_data_file):

    vl_viewer = f'{trial_id}_view_one_vl.html?vl_json='

    # common data and transforms for first layer with marks for each vis model
    base = alt.Chart(os.path.basename(vis_data_file)).transform_calculate(
        rank="format(datum.rank,'03')",
        link=f"'{vl_viewer}' + datum.vl_spec_file"
    ).properties(
        width=250,
        title='visualisation rankings'
    )

    # add a selectable square for each vis model
    select_models = alt.selection_multi(fields=['set', 'rank'])
    squares = base.mark_square(
        size=150
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('rank:O', axis=alt.Axis(title=None)),
        tooltip=['rank:N', 'cost:Q', 'props:N', 'violations:N', 'vl:N'],
        opacity=alt.Opacity('has_match:O', legend=None),
        color=alt.condition(select_models, alt.value('steelblue'), alt.value('lightgray'))
    ).add_selection(
        select_models
    ).interactive()

    # add a small circle with the hyperlink to the actual vis.
    # Shame that xoffset is not an encoding channel, so we have to do in two steps...
    baseline_circles = base.transform_filter(
        datum.set == 'baseline'
    ).mark_circle(
        size=25,
        xOffset=-15,
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('rank:O'),
        tooltip=['link:N'],
        href='link:N'
    ).interactive()

    verde_circles = base.transform_filter(
        datum.set == 'verde'
    ).mark_circle(
        size=25,
        xOffset=15,
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('rank:O'),
        tooltip=['link:N'],
        href='link:N'
    ).interactive()

    # next layer is match lines
    col_domain = ['not', 'with_equal_cost', 'with_different_cost']
    col_range_ = ['steelblue', 'green', 'red']
    match_lines = alt.Chart(os.path.basename(match_data_file)).mark_line().transform_calculate(
        rank="format(datum.rank,'03')"
    ).encode(
        alt.X('set:O', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        alt.Y('rank:O'),
        detail='match:N',
        color=alt.Color('crossed:N', scale=alt.Scale(domain=col_domain, range=col_range_),
                        legend=alt.Legend(orient='bottom'))
    )

    rank_chart = baseline_circles + verde_circles + match_lines + squares

    # chart to show violation occurrences and weights for selected vis models.
    violation_chart = alt.Chart(os.path.basename(violations_data_file)).mark_circle(
        color='red',
    ).transform_calculate(
        rank="format(datum.rank,'03')",
    ).transform_filter(
        select_models
    ).encode(
        x=alt.X('set:N', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        y=alt.Y('violation:N', axis=alt.Axis(title=None)),
        size=alt.Size('num:Q', legend=None),
        opacity=alt.Opacity('cost_contrib:Q', scale=alt.Scale(range=[0, 1]), legend=None),
        #color=alt.Color('cost_contrib:Q', legend=None, scale=alt.Scale(scheme='lightorange')),
        tooltip=['set:N', 'rank:Q', 'violation:N', 'num:Q', 'weight:Q', 'cost_contrib:Q']
    ).properties(
        width=150,
        title='soft rule violations'
    ).interactive()

    # chart to show prop occurrences for selected vis models.
    prop_chart = alt.Chart(os.path.basename(props_data_file)).mark_circle(
        size=50,
        color='green'
    ).transform_calculate(
        rank="format(datum.rank,'03')"
    ).transform_filter(
        select_models
    ).encode(
        x=alt.X('set:N', axis=alt.Axis(labelAngle=0, title=None, orient='top', labelPadding=5)),
        y=alt.Y('prop:N', axis=alt.Axis(title=None)),
        tooltip=['prop:N']
    ).properties(
        width=150,
        title='specification terms'
    ).interactive()

    concat_chart = rank_chart | violation_chart | prop_chart
    concat_chart.save(os.path.join(directory, 'vegalite', f'{trial_id}_view_compare.html'))


create_exploratory_visualisation('trial_01.exp_01',
                                 '../laboratory/trial_01',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_view_compare_model.csv',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_view_compare_match.csv',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_view_compare_violations.csv',
                                 '../laboratory/trial_01/vegalite/trial_01.exp_01_view_compare_props.csv')