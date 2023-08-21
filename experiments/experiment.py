#This code is used ot perform my thesis experiments
import os
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dash_table , dcc
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import json






###### set up Plotly express token #####
px.set_mapbox_access_token(open("token.txt").read())

###### PIPELINE#####

###1/ loading data### 



config_0={'Query_2':[0.01,0.01,0.01,0.01], 'Query_3':[0.32, 0.5, 0.7, 0.84],
 'Query_4':[99.84, 339.87, 778.88, 743.5], 'Query_7': [15.89, 60.28, 134.68, 211.13],
 'Query_9':[144.44, 483.62, 915.93, 1061.65], 'Query_13':[115.88, 431.8, 990.35, 1003.48] }
config_1={'Query_2':[0.02, 0.02, 0.02, 0.02], 'Query_3':[0.17, 0.2, 0.46 , 0.51],
 'Query_4':[27.19, 99.27, 226.98, 446.65], 'Query_7': [2.79 , 10.1, 25.1, 45.47],
 'Query_9':[38.84, 127.85, 286.31, 631.86], 'Query_13':[20.75, 78.99, 179.99, 284.33] }
config_2={'Query_2':[0.06, 0.02, 0.02, 0.02], 'Query_3':[0.15, 0.13, 0.12, 0.18],
 'Query_4':[15.29, 51.47, 115.45, 205.25], 'Query_7': [1.48, 6.17, 12.99, 21.93],
 'Query_9':[16.31, 59.01, 131.76, 287.9], 'Query_13':[11.37, 39.59, 89.61, 143.75] }

config_3={'Query_2':[0.02, 0.02, 0.02, 0.02], 'Query_3':[0.09, 0.12, 0.11, 0.11],
 'Query_4':[8.36, 39.44, 72.01, 121.8], 'Query_7': [0.91, 3.89, 8.18, 13.02],
 'Query_9':[10.15, 35.92, 79.31, 172.35], 'Query_13':[7.18, 27.31, 52.97, 78.57] }

experiment= {'Scale_005':{'Query_2':[0.01, 0.02,0.06,0.02],'Query_3':[0.32,0.17,0.15,0.09],'Query_4':[99.84,27.19,15.29,8.36],
'Query_7':[15.89, 2.79, 1.48,0.91],'Query_9':[144.44,38.84, 16.31,10.15],'Query_13':[115.88, 20.75, 11.37,7.18] },
'Scale_02':{'Query_2':[0.01, 0.02, 0.02,0.02],'Query_3':[0.5, 0.2, 0.13,0.12],'Query_4':[339.87,99.27, 51.47,39.44],
'Query_7':[60.28, 10.1, 6.17,3.89],'Query_9':[483.62, 127.85, 59.01,35.92],'Query_13':[431.8, 78.99, 39.59,27.31] },
'Scale_05':{'Query_2':[0.01, 0.02, 0.02,0.02],'Query_3':[0.7, 0.46, 0.12,0.11], 'Query_4':[778.88, 226.98, 115.45,72.01],
'Query_7':[134.68, 25.1, 12.99,8.18],'Query_9':[915.93, 286.31, 131.76,79.31],'Query_13':[990.35, 179.99, 89.61,52.97] },
'Scale_1':{'Query_2':[0.01, 0.02, 0.02,0.02],'Query_3':[0.84, 0.51, 0.18,0.11],'Query_4':[743.5, 446.65, 205.25,121.8],
'Query_7':[211.13, 45.47, 21.93,13.02],'Query_9':[1061.65, 631.86, 287.9,172.35], 'Query_13':[1003.48, 284.33, 143.75,78.57] }}





##############################################

app = Dash(__name__)



app.layout = html.Div([
 
        html.Div([
            html.H1(children='Benchmarking of geo-spatial and spatio-temporal queries using MobilityDB extension on Google Kubernetes Engine', style={'text-align':'center',"text-decoration": "underline"}),
            html.Br(),
            html.Img(src=app.get_asset_url('mobilitydb-logo.png'), style={'display':'inline-block','height':'30%', 'width':'30%'}),
            html.Img(src=app.get_asset_url('gcp.png'), style={'float':'right','display':'inline-block','height':'30%', 'width':'30%'}),
            html.Br(),
        ]),
    html.Br(),

    html.Div([
        html.H2(children='Overview of query execution time by scale factor and cluster size based on the selected query ID', style={'text-align':'left'}),
        dcc.Dropdown(id='dropdown_query',options=['Query_4', 'Query_7','Query_9','Query_13'], multi=False,
         value="Query_7", style={'width':'200px','display':'inline-block','margin-right':40}, placeholder="Select the query"),
        html.Br(),
        dcc.Graph(id='query_scale_config_id1', figure={}),
        html.Br(),]),
    html.Br(),
     
    html.Div([
        html.H2(children='Overview of BerlinMOD query performance based on the selected scale factor', style={'text-align':'left'}),
        html.Br(),
        dcc.Dropdown(id='dropdown_scale',options=['Scale_005','Scale_02','Scale_05', 'Scale_1',
         ], multi=False,
         value="Scale_005", style={'width':'200px','display':'inline-block','margin-right':40}, placeholder="Select the database scale"),
        dcc.Graph(id='query_scale_config_id2', figure={})
     ]),
    html.Br(),
    html.Div([
        html.H2(children='Overview of the Percentage Improvement PI between 2 configuration', style={'text-align':'left'}),
        html.Br(),
        
        dcc.Graph(id='pi_id', figure={})
     ]),
    html.Br(),
    html.Br(),
    html.Div([
        html.H2(children='AIS benchmark', style={'text-align':'left'}),
        html.Br(),
        
        dcc.Graph(id='ais_bench_id', figure={})
     ]),
    html.Br(),
    html.Br(),
    html.Div([
        html.H2(children='AIS benchmark per query', style={'text-align':'left'}),
        html.Br(),
        dcc.Dropdown(id='ais_query',options=['Query1', 'Query2','Query3'], multi=False,
         value="Query1", style={'width':'200px','display':'inline-block','margin-right':40}, placeholder="Select the AIS query"),

        dcc.Graph(id='ais_bench_per_query', figure={})
     ]),
    html.Br(),
    ])



##############connecting components



@app.callback(
    [Output(component_id='query_scale_config_id1', component_property='figure'),],
    [Input(component_id='dropdown_query', component_property='value'),]
)
def query_time_by_scale_size_figure(query):
    
    res=False
    if query:
        fig= go.Figure()
        fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_0[query],
                        mode='lines+markers',
                        name='1 node')),
        fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_1[query],
                        mode='lines+markers',
                        name='4 nodes'))
        fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_2[query],
                        mode='lines+markers',
                        name='8 nodes'))
        fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_3[query],
                        mode='lines+markers',
                        name='16 nodes'))
        
        fig.update_layout(
        yaxis_title="Execution time (s)",
        xaxis_title="Scale factor (%)",
        xaxis_tickmode='array',
        xaxis_tickvals=[0,0.05,0.2,0.5,1],
        #title='Performance insight of BerlinMOD queries by scale factor and cluster size',
        #font=dict(size=18,color='Black')),
        font=dict(size=18)),
        
        #fig.update_xaxes(range = [0,1])
        """xaxis=dict(
                                title='Xaxis Name',
                                tickmode='array')
                                fig.update_xaxes(fixedrange=True)
                                """
        res =[fig]


       
    return res

title=dict(text="GDP-per-capita", font=dict(size=50), automargin=True, yref='paper')

@app.callback(
    [Output(component_id='query_scale_config_id2', component_property='figure'),],
    [Input(component_id='dropdown_scale', component_property='value'),]
)
def all_queries(scale):
    print("SCALE", experiment[scale].get('Query_2'))
    if scale:
        config1=[ conf[1][0]  for conf in experiment.get(scale).items()]
        config4=[ conf[1][1] for conf in experiment.get(scale).items()]
        config8=[ conf[1][2] for conf in experiment.get(scale).items()]
        config16=[ conf[1][3] for conf in experiment.get(scale).items()]
        #print("SCALE",scale,"config 1 \n", config1," config2 \n",config4, 'config8\n',config8,'config16\n',config16)
        
        figure={ 'data': [
            {'x': [ 'Q4','Q7', 'Q9','Q13'], 'y': config1[2:], 'type': 'bar', 'name': '1 node'},
            {'x': [ 'Q4','Q7', 'Q9','Q13'], 'y': config4[2:], 'type': 'bar', 'name': '4 nodes'},
            {'x': [ 'Q4','Q7', 'Q9','Q13'], 'y': config8[2:], 'type': 'bar', 'name': '8 nodes'},
            {'x': [ 'Q4','Q7', 'Q9','Q13'], 'y': config16[2:], 'type': 'bar', 'name': '16 nodes'},
              
        ],
        'layout': {
            #'title':'Query execution time grouped by cluster size and database scale factor',
            'xaxis':{'title':'Query id'},
            'yaxis':{'title':'Execution time (s)'},
            'font':{'size':20}}
        } 
   
    return [figure]



config_0={
 'Query_4':[99.84, 339.87, 778.88, 743.5], 'Query_7': [15.89, 60.28, 134.68, 211.13],
 'Query_9':[144.44, 483.62, 915.93, 1061.65], 'Query_13':[115.88, 431.8, 990.35, 1003.48] }
config_1={
 'Query_4':[27.19, 99.27, 226.98, 446.65], 'Query_7': [2.79 , 10.1, 25.1, 45.47],
 'Query_9':[38.84, 127.85, 286.31, 631.86], 'Query_13':[20.75, 78.99, 179.99, 284.33] }
config_2={
 'Query_4':[15.29, 51.47, 115.45, 205.25], 'Query_7': [1.48, 6.17, 12.99, 21.93],
 'Query_9':[16.31, 59.01, 131.76, 287.9], 'Query_13':[11.37, 39.59, 89.61, 143.75] }

config_3={
 'Query_4':[8.36, 39.44, 72.01, 121.8], 'Query_7': [0.91, 3.89, 8.18, 13.02],
 'Query_9':[10.15, 35.92, 79.31, 172.35], 'Query_13':[7.18, 27.31, 52.97, 78.57] }

@app.callback(
    [Output(component_id='pi_id', component_property='figure'),],
    [#Input(component_id='dropdown_config1', component_property='value'),
    #Input(component_id='dropdown_config2', component_property='value'),
    Input(component_id='dropdown_scale', component_property='value'),]
)
def compute_pi(scale):

     
    gain_conf1_conf2={
  'Query_4':[((a-b)/a)*100 for a,b in zip(config_0['Query_4'],config_1['Query_4'])],
  'Query_7':[((a-b)/a)*100 for a,b in zip(config_0['Query_7'],config_1['Query_7'])] ,
  'Query_9':[((a-b)/a)*100 for a,b in zip(config_0['Query_9'],config_1['Query_9'])],
  'Query_13':[((a-b)/a)*100 for a,b in zip(config_0['Query_13'],config_1['Query_13'])] }
    
    gain_conf1_conf3={
  'Query_4':[((a-b)/a)*100 for a,b in zip(config_0['Query_4'],config_2['Query_4'])],
  'Query_7':[((a-b)/a)*100 for a,b in zip(config_0['Query_7'],config_2['Query_7'])] ,
  'Query_9':[((a-b)/a)*100 for a,b in zip(config_0['Query_9'],config_2['Query_9'])],
  'Query_13':[((a-b)/a)*100 for a,b in zip(config_0['Query_13'],config_2['Query_13'])] }
    
    gain_conf1_conf4={
  'Query_4':[((a-b)/a)*100 for a,b in zip(config_0['Query_4'],config_3['Query_4'])],
  'Query_7':[((a-b)/a)*100 for a,b in zip(config_0['Query_7'],config_3['Query_7'])] ,
  'Query_9':[((a-b)/a)*100 for a,b in zip(config_0['Query_9'],config_3['Query_9'])],
  'Query_13':[((a-b)/a)*100 for a,b in zip(config_0['Query_13'],config_3['Query_13'])] }
    

    print("config 1...\n",config_0)
    print("config 1...\n",config_1)
    if scale=="Scale_005":
        idx=0
    elif scale=="Scale_02":
        idx=1
    elif scale=="Scale_05":
        idx=2
    elif scale=="Scale_1":
        idx=3


    print("The result.4 node..\n",[gain_conf1_conf2['Query_4'][idx],gain_conf1_conf2['Query_7'][idx],gain_conf1_conf2['Query_9'][idx],gain_conf1_conf2['Query_13'][idx]  ])
    
    print("The result..8 nodes.\n",[gain_conf1_conf3['Query_4'][idx],gain_conf1_conf3['Query_7'][idx],gain_conf1_conf3['Query_9'][idx],gain_conf1_conf3['Query_13'][idx]  ])

    print("The result..16 nodes.\n", [gain_conf1_conf4['Query_4'][idx],gain_conf1_conf4['Query_7'][idx],gain_conf1_conf4['Query_9'][idx],gain_conf1_conf4['Query_13'][idx]  ],)
    fig= go.Figure()
    fig.add_trace(go.Scatter(x=[ 'Q4','Q7', 'Q9','Q13'], y=[gain_conf1_conf2['Query_4'][idx],gain_conf1_conf2['Query_7'][idx],gain_conf1_conf2['Query_9'][idx],gain_conf1_conf2['Query_13'][idx]  ],
                        mode='lines+markers',
                        name='4 nodes')),
    fig.add_trace(go.Scatter(x=[ 'Q4','Q7', 'Q9','Q13'], y=[gain_conf1_conf3['Query_4'][idx],gain_conf1_conf3['Query_7'][idx],gain_conf1_conf3['Query_9'][idx],gain_conf1_conf3['Query_13'][idx]  ],
                        mode='lines+markers',
                        name='8 nodes'))
    fig.add_trace(go.Scatter(x=[ 'Q4','Q7', 'Q9','Q13'], y=[gain_conf1_conf4['Query_4'][idx],gain_conf1_conf4['Query_7'][idx],gain_conf1_conf4['Query_9'][idx],gain_conf1_conf4['Query_13'][idx]  ],
                        mode='lines+markers',
                        name='16 nodes'))
    fig.update_layout(
        yaxis_title="Percentage improvement PI (%)",
        xaxis_title="Query id",
        #title='Performance insight of BerlinMOD queries by scale factor and cluster size',
        #font=dict(size=18,color='Black')),
        font=dict(size=18)),
    return [fig]



@app.callback(
    [Output(component_id='ais_bench_id', component_property='figure'),],
    [Input(component_id='dropdown_scale', component_property='value')]
)
def ais_queries(scale):
    #print("SCALE", experiment[scale].get('Query_2'))
    """if scale:
                        config1=[ conf[1][0]  for conf in experiment.get(scale).items()]
                        config4=[ conf[1][1] for conf in experiment.get(scale).items()]
                        config8=[ conf[1][2] for conf in experiment.get(scale).items()]
                        config16=[ conf[1][3] for conf in experiment.get(scale).items()]
                        #print("SCALE",scale,"config 1 \n", config1," config2 \n",config4, 'config8\n',config8,'config16\n',config16)
                    
    """
    figure={ 'data': [
            {'x': [ 'Q1','Q2', 'Q3'], 'y': [782.56,122.56,720.81], 'type': 'bar', 'name': '1 node'},
            {'x': [ 'Q1','Q2', 'Q3'], 'y': [448.32,43.83,456.34], 'type': 'bar', 'name': '4 nodes'},
            {'x': [ 'Q1','Q2', 'Q3'], 'y': [179.03,32.08,192.2], 'type': 'bar', 'name': '8 nodes'},
            {'x': [ 'Q1','Q2', 'Q3'], 'y': [80.09,10.95,116.72], 'type': 'bar', 'name': '16 nodes'},
              
        ],
        'layout': {
            #'title':'Query execution time grouped by cluster size and database scale factor',
            'xaxis':{'title':'Query id'},
            'yaxis':{'title':'Execution time (s)'},
            'font':{'size':20}}
        } 
    return [figure]




Query1=[782.56,448.32,179.03, 80.09]
Query2=[122.56,43.83,32.08,10.95]
Query3=[720.81,456.34,192.2,116.72]

@app.callback(
    [Output(component_id='ais_bench_per_query', component_property='figure'),],
    [Input(component_id='ais_query', component_property='value'),]
)
def ais_benchmark_exec_time_per_query(query):
    
    res=False
    #fig= go.Figure()
    """if query=='Query1':
                    
                    fig.add_trace(go.Scatter(x=[1,4,8,16], y=Query1,
                                    mode='lines+markers',
                                    )),
                elif query=='Query2':
                    fig.add_trace(go.Scatter(x=[1,4,8,16], y=Query2,
                                    mode='lines+markers',
                                    )),
                else:
                    fig.add_trace(go.Scatter(x=[1,4,8,16], y=Query3,
                                    mode='lines+markers',
                                    )),
    """

    fig= go.Figure()
    fig.add_trace(go.Scatter(x=['Q1','Q2', 'Q3'], y=[782.56,122.56,720.81 ],
                        mode='lines+markers',
                        name='1 nodes')),
    
    fig.add_trace(go.Scatter(x=['Q1','Q2', 'Q3'], y=[448.32,43.83,456.34],
                        mode='lines+markers',
                        name='4 nodes')),
    fig.add_trace(go.Scatter(x=['Q1','Q2', 'Q3'], y=[179.03,32.08,192.2],
                        mode='lines+markers',
                        name='8 nodes'))
    fig.add_trace(go.Scatter(x=['Q1','Q2', 'Q3'], y=[80.09,10.95,116.72],
                        mode='lines+markers',
                        name='16 nodes'))
    fig.update_layout(
        yaxis_title="Execution Time (s)",
        xaxis_title="Query id",
        #title='Performance insight of BerlinMOD queries by scale factor and cluster size',
        #font=dict(size=18,color='Black')),
        font=dict(size=18)),
    """fig.add_trace(go.Scatter(x=[1,4,8,16], y=config_1[query],
                                                mode='lines+markers',
                                                name='4 nodes'))
                                fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_2[query],
                                                mode='lines+markers',
                                                name='8 nodes'))
                                fig.add_trace(go.Scatter(x=[0.05, 0.2,0.5, 1], y=config_3[query],
                                                mode='lines+markers',
                                                name='16 nodes'))
    
    fig.update_layout(
        yaxis_title="Execution time (s)",
        xaxis_title="Cluster size",
        xaxis_tickmode='array',
        xaxis_tickvals=[1,4,8,16],
        #title='Performance insight of BerlinMOD queries by scale factor and cluster size',
        #font=dict(size=18,color='Black')),
        font=dict(size=18)),
    """    
    #fig.update_xaxes(range = [0,1])
    """xaxis=dict(
                                title='Xaxis Name',
                                tickmode='array')
                                fig.update_xaxes(fixedrange=True)
    """
    
    res =[fig]


       
    return res


if __name__ == '__main__':
    app.run_server(debug=True,threaded=True)

