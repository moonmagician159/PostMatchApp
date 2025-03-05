import pandas as pd
import streamlit as st
from PIL import Image
import requests
import io
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
import urllib.request
import numpy as np
from io import StringIO
import matplotlib

cxG = 1.53570624482222

@st.cache_data(ttl=60*15)


def color_percentile(pc):
    rgb = cmap(norm(pc))
    return 'color: #%02x%02x%02x; opacity: 1; textcolor: white' % (int(rgb[0]*100), int(rgb[1]*100), int(rgb[2]*100))
norm = matplotlib.colors.Normalize(vmin=1, vmax=16)
cmap = matplotlib.colormaps['coolwarm']

def get_fotmob_table_data(lg):
     img_base = "https://images.fotmob.com/image_resources/logo/teamlogo"
    
     url = f"https://www.fotmob.com/api/tltable?leagueId={lg_id_dict[lg]}"
     page = requests.get(url)
     soup = BeautifulSoup(page.content, "html.parser")
     json_data = pd.read_json(StringIO(soup.getText()))
    
     table = json_data['data'].apply(lambda x: x['table']).apply(lambda x: x['all'])
     df = pd.json_normalize(table)
     df = df.T
    
     df_all = pd.DataFrame()
     for i in range(len(df)):
         for j in range(len(df.columns)):
             row = pd.DataFrame(pd.Series(df.iloc[i,j])).T
             df_all = pd.concat([df_all,row])
     df_all.reset_index(drop=True,inplace=True)
    
     df_all['logo'] = [f"{img_base}/{df_all['id'][i]}.png" for i in range(len(df_all))]
     df_all['goals'] = [int(df_all['scoresStr'][i].split("-")[0]) for i in range(len(df_all))]
     df_all['conceded_goals'] = [int(df_all['scoresStr'][i].split("-")[1]) for i in range(len(df_all))]
     df_all['real_position'] = df_all['idx']
     df_all.sort_values(by=['real_position'],ascending=True,inplace=True)
     df_all.reset_index(drop=True,inplace=True)
     df_all['Goals per match'] = [df_all['goals'][i]/df_all['played'][i] if df_all.played[i]>0 else 0 for i in range(len(df_all))]
     df_all['Goals against per match'] = [df_all['conceded_goals'][i]/df_all['played'][i] if df_all.played[i]>0 else 0 for i in range(len(df_all))]
    
     tables = df_all[['real_position','name','played','wins','draws','losses','pts','goals','conceded_goals','goalConDiff','logo']].rename(columns={
         'pts':'Pts',
         'name':'Team',
         'real_position':'Pos',
         'xg':'xG',
         'xgConceded':'xGA',
         'goals':'GF',
         'conceded_goals':'GA',
         'played':'M',
         'wins':'W',
         'draws':'D',
         'losses':'L',
         'goalConDiff':'GD'
     })
     tables[['Pts','GF','GA','Pos','M']] = tables[['Pts','GF','GA','Pos','M']].astype(int)
     logos = tables.logo.tolist()[::-1]
     tables = tables.iloc[:,:-1]
    
     tables.rename(columns={'Pos':' '},inplace=True)
    
     indexdf = tables[::-1].copy()

     return indexdf, logos

def create_fotmob_table_img(lg, date, indexdf, logos):
     plt.clf()
     sns.set(rc={'axes.facecolor':'#fbf9f4', 'figure.facecolor':'#fbf9f4',
                'ytick.labelcolor':'#4A2E19', 'xtick.labelcolor':'#4A2E19'})
    
    
     fig = plt.figure(figsize=(5,6), dpi=200)
     ax = plt.subplot()
    
     ncols = len(indexdf.columns.tolist())+1
     nrows = indexdf.shape[0]
    
     ax.set_xlim(0, ncols + .5)
     ax.set_ylim(0, nrows + 1.5)
    
     positions = [0.75, 1.2, 5, 5.75, 6.5, 7.25, 8, 8.75, 9.5, 10.25]
     columns = indexdf.columns.tolist()
    
     for i in range(nrows):
         for j, column in enumerate(columns):
             text_label = f'{indexdf[column].iloc[i]}'
             weight = 'regular'
             ax.annotate(
                 xy=(positions[j], i + .5),
                 text = text_label.replace(' U18',''),
                 ha='left',
                 va='center', color='#4A2E19',
                 weight=weight,
                 size=7.5
             )
    
     column_names = columns
     for index, c in enumerate(column_names):
             ax.annotate(
                 xy=(positions[index], nrows + .25),
                 text=column_names[index],
                 ha='left',
                 va='bottom',
                 weight='bold', color='#4A2E19',
                 size=7.5
             )
    
     ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [nrows, nrows], lw=1.5, color='black', marker='', zorder=4)
     ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0], lw=1.5, color='black', marker='', zorder=4)
     for x in range(1, nrows):
         ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [x, x], lw=.5, color='gray', ls=':', zorder=3 , marker='')
    
     ax.set_axis_off()
    
     DC_to_FC = ax.transData.transform
     FC_to_NFC = fig.transFigure.inverted().transform
     DC_to_NFC = lambda x: FC_to_NFC(DC_to_FC(x))
     ax_point_1 = DC_to_NFC([2.25, 0.25])
     ax_point_2 = DC_to_NFC([2.75, 0.75])
     ax_width = abs(ax_point_1[0] - ax_point_2[0])
     ax_height = abs(ax_point_1[1] - ax_point_2[1])
     def ax_logo(link, ax):
        response = requests.get(link, stream=True)
        response.raise_for_status()
        club_icon = Image.open(io.BytesIO(response.content))
        ax.imshow(club_icon)
        ax.axis('off')
        return ax

     for x in range(0, nrows):
         ax_coords = DC_to_NFC([0, x + .25])
         ax = fig.add_axes(
             [ax_coords[0], ax_coords[1], ax_width, ax_height]
         )
         ax_logo(logos[x], ax)
    
     fig.text(
         x=0.15, y=.91,
         s=f'{lg} Table',
         ha='left',
         va='bottom',
         weight='bold',
         size=11, color='#4A2E19'
     )
     fig.text(
         x=0.15, y=.9,
         s=f'Table is from FotMob | football-match-reports.streamlit.app',
         ha='left',
         va='top',
         weight='regular',
         size=6, color='#4A2E19'
     )

     return fig

def add_mov_avg(df,var):
    df['4-Match Moving Average'] = np.nan
    for i in range(len(df)):
        if i+4 <= len(df):
            df.loc[i, '4-Match Moving Average'] = df[var][i:i+4].mean()
    return df


nbi_links = pd.read_csv("https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/NBI_Match_Links.csv")
lg_lookup = pd.read_csv("https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/PostMatchLeagues.csv")
league_list = lg_lookup.League.unique().tolist()
lg_lookup = pd.read_csv("https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/PostMatchLeagues.csv")
lg_id_dict = {lg_lookup.League[i]: lg_lookup.FotMob[i] for i in range(len(lg_lookup))}


with st.sidebar:
    lgg = st.selectbox('What League Do You Want Reports For?', league_list)
    season = st.selectbox('Season', (sorted(lg_lookup[lg_lookup.League == lgg].Season.unique().tolist(),reverse=True)))
    
update_date = lg_lookup[(lg_lookup.League==lgg) & (lg_lookup.Season==season)].Update.values[0]
league = lgg.replace("ü","u").replace("ó","o").replace("è","e")
    
st.title(f"{lgg} {season} Post-Match Reports")
st.subheader(f"Last Updated: {update_date}\n")
st.subheader('All data via Opta')

df = pd.read_csv(f"https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/League_Files/{league.replace(' ','%20')}%20Full%20Match%20List%20{season}.csv")
df['Match_Name'] = df['Match'] + ' ' + df['Date']



with st.sidebar:
    team_list = sorted(list(set(df.Home.unique().tolist() + df.Away.unique().tolist())))
    team = st.selectbox('What team are you researching?', team_list)

    specific = st.selectbox('Specific Match or Most Recent Matches?', ('Specific Match','Recent Matches'))
    if specific == 'Specific Match':
        match_list = df[(df.Home == team) | (df.Away == team)].copy()
        match_choice = st.selectbox('Match', match_list.Match_Name.tolist())
        render_matches = [match_choice]
    if specific == 'Recent Matches':
        match_list = df[(df.Home == team) | (df.Away == team)].copy()
        num_matches = st.slider('Number of Recent Matches', min_value=1, max_value=5, value=3)
        render_matches = match_list.head(num_matches).Match_Name.tolist()

    focal_color = st.color_picker("Pick a color to highlight the team on League Ranking tab", "#4c94f6")

try:
     with st.sidebar:
         st.write(f"{lgg} Table (via FotMob)")
         table_indexdf, table_logos = get_fotmob_table_data(lgg)
         st.table(table_indexdf[::-1].reset_index(drop=True).rename(columns={' ':'Pos.'}))
except:
     pass

#########################
def ben_theme():
    return {
        'config': {
            'background': '#fbf9f4',
            # 'text': '#4a2e19',
            # 'mark': {
            #     'color': focal_color,
            # },
            'axis': {
                'titleColor': '#4a2e19',
                'labelColor': '#4a2e19',
            },
            'text': {
                'fill': '#4a2e19'
            },
            'title': {
                'color': '#4a2e19',
                'subtitleColor': '#4a2e19'
            }
        }
    }

# register the custom theme under a chosen name
alt.themes.register('ben_theme', ben_theme)

# enable the newly registered theme
alt.themes.enable('ben_theme')
################################

report_tab, data_tab, graph_tab, rank_tab, full_ranks_tab, xg_tab, scatter_tab = st.tabs(['Match Report', 'Data by Match - Table', 'Data by Match - Graph', 'League Rankings', 'Full League Ranks', 'xG & xGA By Match', 'Variable Scatters'])

for i in range(len(render_matches)):
    try:
        match_string = render_matches[i].replace(' ','%20')
        if league == 'NB I':
            nbi_game_link = nbi_links[nbi_links.MatchName==render_matches[i]]['URL'].values[0]
            with report_tab:
                st.write(f'Link to Full Match Video (some games may not have been shown on M4Sport and therefore are not available):  \n  \n{render_matches[i][:-11]} -> {nbi_game_link}')
        url = f"https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/Image_Files/{league.replace(' ','%20')}%20{season}/{match_string}.png"
        response = requests.get(url)
        game_image = Image.open(io.BytesIO(response.content))
        report_tab.image(game_image)
    except:
        st.write(f"Apologies, {render_matches[i]} must not be available yet. Please check in later!")

team_data = pd.read_csv(f"https://raw.githubusercontent.com/moonmagician159/Post_Match_App/main/Stat_Files/{league.replace(' ','%20')}%20{season}.csv")

conditions_team = [
    team_data['Goals'] > team_data['Goals Conceded'],
    team_data['Goals'] < team_data['Goals Conceded']]
choices_team = ['W', 'L']
team_data['Result'] = np.select(conditions_team, choices_team, default='D')
conditions_team = [
    team_data['Goals'] > team_data['Goals Conceded'],
    team_data['Goals'] < team_data['Goals Conceded']]
choices_team = [3, 0]
team_data['Pts'] = np.select(conditions_team, choices_team, default=1)

team_data['Field Tilt - Possession'] = team_data['Field Tilt'] - team_data['Possession']
team_data['xT Difference'] = team_data['xT'] - team_data['xT Against']

gc_lookup = team_data.groupby(['Match','Date'])['Game Control'].sum().reset_index()
team_data['Game Control Share'] = [round(100*team_data['Game Control'][i]/gc_lookup[(gc_lookup.Match==team_data.Match[i]) & (gc_lookup.Date==team_data.Date[i])]['Game Control'].values[0],2) for i in range(len(team_data))]

team_data['xPts'] = [3 * ((team_data['xG'][i]**cxG)/((team_data['xG'][i]**cxG)+(team_data['xGA'][i]**cxG))) for i in range(len(team_data))]
team_data['Pts-xPts'] = team_data['Pts'] - team_data['xPts']
team_data[['xPts','Pts-xPts']] = round(team_data[['xPts','Pts-xPts']],2)

league_data = team_data.copy().reset_index(drop=True)
team_data = team_data[team_data.Team==team].reset_index(drop=True)

team_data['Shots per 1.0 xT'] = team_data['Shots per 1.0 xT'].astype(float)
team_data.rename(columns={'Shots per 1.0 xT':'Shots per 1 xT'},inplace=True)
team_data['Shots Faced per 1.0 xT Against'] = team_data['Shots Faced per 1.0 xT Against'].astype(float)
team_data.rename(columns={'Shots Faced per 1.0 xT Against':'Shots Faced per 1 xT Against'},inplace=True)

league_data['Shots per 1.0 xT'] = league_data['Shots per 1.0 xT'].astype(float)
league_data.rename(columns={'Shots per 1.0 xT':'Shots per 1 xT'},inplace=True)
league_data['Shots Faced per 1.0 xT Against'] = league_data['Shots Faced per 1.0 xT Against'].astype(float)
league_data.rename(columns={'Shots Faced per 1.0 xT Against':'Shots Faced per 1 xT Against'},inplace=True)


team_data['xG per 1 xT'] = team_data['xG']/team_data['xT']
league_data['xG per 1 xT'] = league_data['xG']/league_data['xT']
team_data['Open Play xG per 1 xT'] = team_data['Open Play xG']/team_data['xT']
league_data['Open Play xG per 1 xT'] = league_data['Open Play xG']/league_data['xT']

team_data['xGA per 1 xT Against'] = team_data['xGA']/team_data['xT Against']
league_data['xGA per 1 xT Against'] = league_data['xGA']/league_data['xT Against']
team_data['Open Play xGA per 1 xT Against'] = team_data['Open Play xGA']/team_data['xT Against']
league_data['Open Play xGA per 1 xT Against'] = league_data['Open Play xGA']/league_data['xT Against']

available_vars = ['Possession',
                  'xG','xGA','xGD',
                  'Open Play xG','Open Play xGA','Open Play xGD',
                  'Set Piece xG','Set Piece xGA','Set Piece xGD',
                  'npxG','npxGA','npxGD',
                  'GD','GD-xGD',
                  'xPts','Pts-xPts',
                  'Goals','Goals Conceded',
                  'Shots','Shots Faced','Field Tilt','Field Tilt - Possession','Avg Pass Height','Passes in Opposition Half','Passes into Box','xT','xT Against','xT Difference','Shots per 1 xT','Shots Faced per 1 xT Against',
                  'xG per 1 xT','xGA per 1 xT Against',
                  'Open Play xG per 1 xT','Open Play xGA per 1 xT Against',
                  'PPDA','High Recoveries','High Recoveries Against','Crosses','Corners','Fouls',
                 'Throw-Ins into the Box','On-Ball Pressure','On-Ball Pressure Share','Off-Ball Pressure','Off-Ball Pressure Share','Game Control','Game Control Share',
                 ]

rank_vars = ['xPts','Possession','Field Tilt','Goals','Goals Conceded','Open Play xG','Open Play xGA','xT Difference','Open Play xG per 1 xT','PPDA','High Recoveries','High Recoveries Against',]
rank_tfs = [False,False,False,False,True,False,True,False,False,True,False,True]
rank_tfs_inv = [True,True,True,True,False,True,False,True,True,False,True,False]


team_data[available_vars] = team_data[available_vars].astype(float)
league_data[available_vars] = league_data[available_vars].astype(float)

league_data_base = league_data.copy()

data_tab.write(team_data)

with graph_tab:
    plot_type = st.radio("Line or Bar plot?", ['📈 Line', '📊 Bar'])
    var = st.selectbox('Metric to Plot', available_vars)
    mov_avg = st.radio("Add a 4-Match Moving Average Line?", ['Yes', 'No'])
    team_data2 = add_mov_avg(team_data,var)

    if plot_type == '📈 Line':
        lg_avg_var = league_data[var].mean()
        team_avg_var = team_data[var].mean()
        
        c = (alt.Chart(
                team_data2[::-1],
                title={
                    "text": [f"{team} {var}, {league}"],
                    "subtitle": [f"Data via Opta as of {update_date}"]
                }
            )
            .mark_line(point=True, color='#4c94f6')
            .encode(
                x=alt.X('Date', sort=None),
                y=alt.Y(var, scale=alt.Scale(zero=False)),
                tooltip=['Match', 'Date', var, 'Possession','Field Tilt']
            )
        )
    
        lg_avg_line = alt.Chart(pd.DataFrame({'y': [lg_avg_var]})).mark_rule(color='#ee5454').encode(y='y')
        
        lg_avg_label = lg_avg_line.mark_text(
            x="width",
            dx=-2,
            align="right",
            baseline="bottom",
            text="League Avg",
            color='#ee5454'
        )
    
        team_avg_line = alt.Chart(pd.DataFrame({'y': [team_avg_var]})).mark_rule(color='#f6ba00').encode(y='y')
        
        team_avg_label = team_avg_line.mark_text(
            x="width",
            dx=-2,
            align="right",
            baseline="bottom",
            text="Team Avg",
            color='#f6ba00'
        )

        if mov_avg == 'Yes':
            mov_avg_line = (alt.Chart(
                    team_data2[::-1],
                )
                .mark_line(point=False, color='#4a2e19', strokeDash=[8,8])
                .encode(
                    x=alt.X('Date', sort=None),
                    y=alt.Y('4-Match Moving Average', scale=alt.Scale(zero=False)),
                    tooltip=['Match', 'Date', '4-Match Moving Average']
                )
            )
            
            chart = (c + lg_avg_line + lg_avg_label + team_avg_line + team_avg_label + mov_avg_line)
        if mov_avg == 'No':
            chart = (c + lg_avg_line + lg_avg_label + team_avg_line + team_avg_label)
            
        chart.layer[0].encoding.y.title = var
        st.altair_chart(chart, use_container_width=True)

    if plot_type == '📊 Bar':
        lg_avg_var = league_data[var].mean()
        team_avg_var = team_data[var].mean()

        c = (alt.Chart(
                team_data[::-1],
                title={
                    "text": [f"{team} {var}, {league}"],
                    "subtitle": [f"Data via Opta as of {update_date}"]
                }
            )
            .mark_bar()
            .encode(
                x=alt.X('Date', sort=None),
                y=alt.Y(var, scale=alt.Scale(zero=False)), 
                color=alt.condition(alt.datum[var] >= 0, alt.value('#4c94f6'), alt.value('#ee5454')),
                tooltip=['Match', 'Date', var, 'Possession','Field Tilt']
            )
        )

        if var not in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
            lg_avg_line = alt.Chart(pd.DataFrame({'y': [lg_avg_var]})).mark_rule(color='#ee5454').encode(y='y')
            
            lg_avg_label = lg_avg_line.mark_text(
                x="width",
                dx=-2,
                align="right",
                baseline="bottom",
                text="League Avg",
                color='#ee5454'
            )
        if var in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
            lg_avg_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='k').encode(y='y')
    
        team_avg_line = alt.Chart(pd.DataFrame({'y': [team_avg_var]})).mark_rule(color='#f6ba00').encode(y='y')
        
        team_avg_label = team_avg_line.mark_text(
            x="width",
            dx=-2,
            align="right",
            baseline="bottom",
            text="Team Avg",
            color='#f6ba00'
        )
    

        if mov_avg == 'Yes':
            mov_avg_line = (alt.Chart(
                    team_data2[::-1],
                )
                .mark_line(point=False, color='#4a2e19', strokeDash=[8,8])
                .encode(
                    x=alt.X('Date', sort=None),
                    y=alt.Y('4-Match Moving Average', scale=alt.Scale(zero=False)),
                    tooltip=['Match', 'Date', '4-Match Moving Average']
                )
            )
            if var not in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
                chart = (c + lg_avg_line + lg_avg_label + team_avg_line + team_avg_label + mov_avg_line)
            if var in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
                chart = (c + lg_avg_line + team_avg_line + team_avg_label + mov_avg_line)

        if mov_avg == 'No':
            if var not in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
                chart = (c + lg_avg_line + lg_avg_label + team_avg_line + team_avg_label)
            if var in ['xT Difference','GD-xGD','Pts-xPts','npxGD','Open Play xGD','Set Piece xGD']:
                chart = (c + lg_avg_line + team_avg_line + team_avg_label)

        chart.layer[0].encoding.y.title = var
        st.altair_chart(chart, use_container_width=True)


with rank_tab:
    ranking_base_df = league_data_base.copy()
    rank_method = st.selectbox('Ranking Method', ['Average','Total','Median'])
    rank_var = st.selectbox('Metric to Rank', available_vars)

    if rank_method == 'Median':
        rank_df = ranking_base_df.groupby(['Team'])[available_vars].median().reset_index()
    if rank_method == 'Total':
        rank_df = ranking_base_df.groupby(['Team'])[available_vars].sum().reset_index()
    if rank_method == 'Average':
        rank_df = ranking_base_df.groupby(['Team'])[available_vars].mean().reset_index()

    if rank_var in ['Open Play xGA per 1 xT Against','xGA','Set Piece xGA','Open Play xGA','npxGA','Goals Conceded','Shots Faced','xT Against','xGA per 1 xT Against','PPDA','Fouls','High Recoveries Against', 'Shots Faced per 1 xT Against']:
        sort_method = True
    else:
        sort_method = False

    indexdf_short = rank_df.sort_values(by=[rank_var],ascending=sort_method)[['Team',rank_var]].reset_index(drop=True)[::-1]
    
    sns.set(rc={'axes.facecolor':'#fbf9f4', 'figure.facecolor':'#fbf9f4',
           'ytick.labelcolor':'#4A2E19', 'xtick.labelcolor':'#4A2E19'})

    fig = plt.figure(figsize=(7,8), dpi=200)
    ax = plt.subplot()
    
    ncols = len(indexdf_short.columns.tolist())+1
    nrows = indexdf_short.shape[0]

    ax.set_xlim(0, ncols + .5)
    ax.set_ylim(0, nrows + 1.5)
    
    positions = [0.05, 2.0]
    columns = indexdf_short.columns.tolist()
    
    # Add table's main text
    for i in range(nrows):
        for j, column in enumerate(columns):
            if column == 'Team':
                if nrows-i < 10:
                    text_label = f'{nrows-i}     {indexdf_short[column].iloc[i]}'
                else:
                    text_label = f'{nrows-i}   {indexdf_short[column].iloc[i]}'
            else:
                text_label = f'{round(indexdf_short[column].iloc[i],2)}'
            if indexdf_short['Team'].iloc[i] == team:
                t_color = focal_color
                weight = 'bold'
            else:
                t_color = '#4A2E19'
                weight = 'regular'
            ax.annotate(
                xy=(positions[j], i + .5),
                text = text_label,
                ha='left',
                va='center', color=t_color,
                weight=weight
            )
            
    # Add column names
    column_names = columns
    for index, cs in enumerate(column_names):
            ax.annotate(
                xy=(positions[index], nrows + .25),
                text=column_names[index],
                ha='left',
                va='bottom',
                weight='bold', color='#4A2E19'
            )

    # Add dividing lines
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [nrows, nrows], lw=1.5, color='black', marker='', zorder=4)
    ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [0, 0], lw=1.5, color='black', marker='', zorder=4)
    for x in range(1, nrows):
        ax.plot([ax.get_xlim()[0], ax.get_xlim()[1]], [x, x], lw=1.15, color='gray', ls=':', zorder=3 , marker='')
    
    ax.set_axis_off()
    
    DC_to_FC = ax.transData.transform
    FC_to_NFC = fig.transFigure.inverted().transform
    # -- Take data coordinates and transform them to normalized figure coordinates
    DC_to_NFC = lambda x: FC_to_NFC(DC_to_FC(x))
    # -- Add nation axes
    ax_point_1 = DC_to_NFC([2.25, 0.25])
    ax_point_2 = DC_to_NFC([2.75, 0.75])
    ax_width = abs(ax_point_1[0] - ax_point_2[0])
    ax_height = abs(ax_point_1[1] - ax_point_2[1])

    fig.text(
        x=0.14, y=.91,
        s=f"{rank_var} {rank_method} Rankings",
        ha='left',
        va='bottom',
        weight='bold',
        size=13, color='#4A2E19'
    )
    fig.text(
        x=0.14, y=.9,
        s=f"Data via Opta as of {update_date}  \n",
        ha='left',
        va='top',
        weight='regular',
        size=11, color='#4A2E19'
    )

    fig

with full_ranks_tab:
    sort_var = st.selectbox('Metric to Sort By', rank_vars)
    league_data_rank_base = league_data.copy()

    league_ranks = league_data_base.groupby(['Team'])[rank_vars].mean()
    
    for i in range(len(rank_vars)):
        league_ranks[rank_vars[i]] = league_ranks[rank_vars[i]].rank(ascending=rank_tfs[i])
    
    league_ranks[rank_vars] = league_ranks[rank_vars].astype(int)
    
    league_ranks = league_ranks.sort_values(by=[sort_var],ascending=rank_tfs_inv[rank_vars.index(sort_var)])
    
    norm = matplotlib.colors.Normalize(vmin=1, vmax=len(league_ranks))
    st.dataframe(league_ranks.T.style.map(color_percentile))

with xg_tab:
    scatter_select = st.radio("Expected Goals (xG) or Expected Threat (xT)?", ['⚽ xG', '⚡ xT'])
    
    if scatter_select == '⚽ xG':
        xvar, yvar, diffvar = 'xG', 'xGA', 'xGD'
    elif scatter_select == '⚡ xT':
        xvar, yvar, diffvar = 'xT', 'xT Against', 'xT Difference'
    
    lg_chart_xg = alt.Chart(league_data,  title=alt.Title(
       f"{team} {xvar} & {yvar} by Match, {league}",
       subtitle=[f"Data via Opta as of {update_date}",f"Small grey points are all matches in the league. Large Colored points are {team}'s matches","Generated on: football-match-reports.streamlit.app"],
    )).mark_circle(size=30, color='silver').encode(
        x=xvar,
        y=yvar,
        tooltip=['Team','Match','Date',xvar,yvar,diffvar,'Possession','Field Tilt']
    ).properties(height=500).interactive()
    
    domain = ['W','D','L']
    range_ = ['blue','black','darkorange']
    team_chart_xg = alt.Chart(team_data,  title=alt.Title(
       f"{team} {xvar} & {yvar} by Match, {league}",
       subtitle=[f"Data via Opta as of {update_date}",f"Small grey points are all matches in the league. Large Colored points are {team}'s matches","Generated on: football-match-reports.streamlit.app"],
    )).mark_circle(size=90).encode(
        x=xvar,
        y=yvar,
        color=alt.Color('Result').scale(domain=domain, range=range_),
        tooltip=['Team','Match','Date',xvar,yvar,diffvar,'Possession','Field Tilt']
    ).properties(height=500).interactive()
    
    line = pd.DataFrame({
        xvar: [0, max(league_data[xvar])],
        yvar: [0, max(league_data[yvar])],
    })
    
    line_plot_xg = alt.Chart(line).mark_line(color='grey', size=1).encode(
        x=xvar,
        y=yvar
    )
    
    
    chart_xg = (lg_chart_xg + team_chart_xg + line_plot_xg)

    st.altair_chart(chart_xg, use_container_width=True)

with scatter_tab:
    xvar = st.selectbox('X-Axis Variable', available_vars)
    rank_method_x = st.radio("X-Axis Method", ['Average','Total','Median'])
    yvar = st.selectbox('Y-Axis Variable', available_vars)
    rank_method_y = st.radio("Y-Axis Method", ['Average','Total','Median'])
    
    league_scatter = league_data_base.copy()
    
    if rank_method_x == 'Median':
        league_scatter_x = league_scatter.groupby(['Team'])[xvar].median().reset_index()
    if rank_method_x == 'Total':
        league_scatter_x = league_scatter.groupby(['Team'])[xvar].sum().reset_index()
    if rank_method_x == 'Average':
        league_scatter_x = league_scatter.groupby(['Team'])[xvar].mean().reset_index()
    
    if rank_method_y == 'Median':
        league_scatter_y = league_scatter.groupby(['Team'])[yvar].median().reset_index()
    if rank_method_y == 'Total':
        league_scatter_y = league_scatter.groupby(['Team'])[yvar].sum().reset_index()
    if rank_method_y == 'Average':
        league_scatter_y = league_scatter.groupby(['Team'])[yvar].mean().reset_index()
    
    league_scatter = league_scatter_x.merge(league_scatter_y)
    team_scatter = league_scatter[league_scatter.Team==team]
    
    lg_chart_scatter = alt.Chart(league_scatter,  title=alt.Title(
       f"{league}, {rank_method_x} {xvar} & {rank_method_y} {yvar}",
       subtitle=[f"Data via Opta as of {update_date}",f"Colored point indicates {team}","Generated on: football-match-reports.streamlit.app"],
    )).mark_circle(size=75, color='grey').encode(
        x=alt.X(xvar).scale(zero=False),
        y=alt.Y(yvar).scale(zero=False),
        # color='Result',
        tooltip=['Team',xvar,yvar,]
    ).properties(height=500).interactive()

    team_chart_scatter = alt.Chart(team_scatter,  title=alt.Title(
       f"{league}, {rank_method_x} {xvar} & {rank_method_y} {yvar}",
       subtitle=[f"Data via Opta as of {update_date}",f"Colored point indicates {team}","Generated on: football-match-reports.streamlit.app"],
    )).mark_circle(size=125,color=focal_color).encode(
        x=alt.X(xvar).scale(zero=False),
        y=alt.Y(yvar).scale(zero=False),
        # color=alt.Color('Result').scale(domain=domain, range=range_),
        tooltip=['Team',xvar,yvar,]
    ).properties(height=500).interactive()
    
    
    scatter_chart = (lg_chart_scatter + team_chart_scatter)
    
    st.altair_chart(scatter_chart, use_container_width=True)


