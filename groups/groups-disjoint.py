#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
from scipy.sparse.linalg import svds
import itertools
import warnings
warnings.filterwarnings('ignore')

print("Loading...")
followers_df_all = pd.read_table('../input/user_sns.txt', names=('follower', 'followee'))
print("Loaded")


##### disjoint
id_from = 1000000
#id_to = 1100000 #914 group
#id_to = 1046170 #100 group
id_to = 1025000 #[5 group]
#id_to = 1021000 #5 gruop
#id_to = 1019000 #3 gruop
#id_to = 1011000 #1 group
#id_to = 1146580
#id_to = 1079100 #100 group (10)
#id_to = 1072733
limit = 5
#limit = 10

df = followers_df_all[followers_df_all["followee"] > id_from]
upper = df[df["followee"] <= id_to]
lower = upper[upper["follower"] > id_from]
followers_df = lower[lower["follower"] <= id_to]

#users who belongs to a group whose size is greater than or equal to 5
followers_count_df = followers_df.groupby(['follower']).size()
followers_with_enough_followees_df = followers_count_df[ followers_count_df >= limit].reset_index()[['follower']]
selected_df =  followers_df.merge(followers_with_enough_followees_df,
               how = 'right',
               left_on = 'follower',
               right_on = 'follower')

groups_tmp = selected_df.groupby('follower')['followee'].apply(list)

# append self
for send_from in groups_tmp.keys():
    groups_tmp[send_from].append(send_from)

d = {}
client_list = []
for send_from in groups_tmp.keys():
    l = []
    g = groups_tmp[send_from]
    for c in g:
        if c not in client_list:
            l.append(c)
        if send_from in l and len(l) >= limit+1:
            l.remove(send_from)
            client_list.extend(l)
            d[send_from] = l
        elif send_from not in l and len(l) >= limit:
            client_list.extend(l)
            d[send_from] = l

groups = pd.Series(data=d, name='followee') 
groups_comb = pd.Series(data=d, name='followee')
groups_for_viz = pd.Series(data=d, name='followee') 
groups_df = pd.DataFrame(groups).reset_index()

# append self
for send_from in groups_comb.keys():
    #groups[send_from].append(send_from)
    groups_comb[send_from].append(send_from)

# extract all possible pairs in the group
for send_from in groups_comb.keys():
  #groups[send_from] = list(itertools.permutations(groups[send_from],2))
  groups_comb[send_from] = list(itertools.combinations(groups_comb[send_from],2))

print("Done")

tmp_nodes = set()
edges = set()
for g in groups_comb:
    for p in g:
        edges.add(p)
        tmp_nodes.add(p[0]); tmp_nodes.add(p[1])
edges = list(edges)

clients_df = pd.read_csv("./disjoint/client-group-5-doc-1-loc-1-cluster-4-method-RA.csv", names = ["application_id", "client_id", "x", "y", "home_id"])
nodes = list()
for i in range(len(clients_df)):
    if clients_df.iloc[i]["client_id"] in tmp_nodes:
        nodes.append((clients_df.iloc[i]["client_id"], {"pos" : [clients_df.iloc[i]["x"], clients_df.iloc[i]["y"]]}))



import plotly.graph_objects as go

import networkx as nx
import psutil

G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = G.nodes[edge[0]]['pos']
    x1, y1 = G.nodes[edge[1]]['pos']
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1.0, color='#888'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
for node in G.nodes():
    x, y = G.nodes[node]['pos']
    node_x.append(x)
    node_y.append(y)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        # colorscale options
        #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        colorscale='YlGnBu',
        reversescale=False,
        color=[],
        size=15,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))

node_adjacencies = []
node_text = []
for node, adjacencies in enumerate(G.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    node_text.append('# of connections: '+str(len(adjacencies[1])))

node_trace.marker.color = node_adjacencies
node_trace.text = node_text

fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                titlefont_size=16,
                font_size=24,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                width = 1000,
                height = 1000,
                #annotations=[ dict(
                #    showarrow=False,
                #    xref="paper", yref="paper",
                #    x=0.005, y=-0.002 ) ],
                xaxis=dict(range=[0,25],showgrid=True, zeroline=True, showticklabels=True, title = 'x (km)'),
                yaxis=dict(range=[0,25],showgrid=True, zeroline=True, showticklabels=True, title = 'y (km)')
             )
        )
                

                #fig.to_image(format="png", engine="kaleido")
print("saving...")
fig.write_image("./disjoint/group5_limit5.png")



import seaborn as sns

groups_df["size"] = 0
for i, row in enumerate(groups_df["followee"]):
    groups_df["size"][i] = len(row)

sns.set(rc={'figure.figsize':(11.7,8.27)})
ax = sns.histplot(data = groups_df, x = "size", binwidth = 1)
ax.figure.savefig("./disjoint/group5_limit5_hist.png")




