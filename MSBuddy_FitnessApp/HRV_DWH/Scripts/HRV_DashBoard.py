"""
Interactive HRV Analytics Dashboard
Built with Dash and Plotly for comprehensive HRV monitoring and analysis
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from HRV_dwhAnalytics_v2 import HRVAnalytics  # Import our analytics class

# Initialize the dashboard
app = dash.Dash(__name__)
app.title = "HRV Analytics Dashboard"

# Initialize HRV Analytics
hrv_analytics = HRVAnalytics("c:/smakrykoDBs/Mercury_DWH_HRV.db")

# Define the dashboard layout
app.layout = html.Div([
    # Header Section
    html.Div([
        html.H1("❤️ HRV Analytics Dashboard", 
                style={'textAlign': 'center', 'color': '#2E86AB', 'marginBottom': '30px'}),
        html.P("Heart Rate Variability Monitoring & Recovery Analysis", 
               style={'textAlign': 'center', 'fontSize': '18px', 'color': '#666'})
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Control Panel
    html.Div([
        html.Div([
            html.Label("📅 Analysis Period:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='days-dropdown',
                options=[
                    {'label': '7 Days', 'value': 7},
                    {'label': '14 Days', 'value': 14},
                    {'label': '30 Days', 'value': 30},
                    {'label': '60 Days', 'value': 60},
                    {'label': '90 Days', 'value': 90}
                ],
                value=30,
                style={'marginBottom': '15px'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'paddingRight': '20px'}),
        
        html.Div([
            html.Label("📱 HRV Source:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='source-dropdown',
                options=[
                    {'label': 'F3b Monitor+HRV', 'value': 'F3b Monitor+HRV'},
                    {'label': 'Polar H10', 'value': 'Polar H10'},
                    {'label': 'Oura Ring', 'value': 'Oura Ring'},
                    {'label': 'All Sources', 'value': 'All'}
                ],
                value='F3b Monitor+HRV',
                style={'marginBottom': '15px'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'paddingRight': '20px'}),
        
        html.Div([
            html.Button("🔄 Refresh Data", id='refresh-button', n_clicks=0,
                       style={'backgroundColor': '#28a745', 'color': 'white', 'border': 'none',
                              'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer'})
        ], style={'width': '30%', 'display': 'inline-block', 'textAlign': 'right'})
    ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'marginBottom': '20px', 
              'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Key Metrics Summary Cards
    html.Div(id='summary-cards', style={'marginBottom': '20px'}),
    
    # Main Visualizations
    html.Div([
        # Time Domain & Recovery Scores
        html.Div([
            dcc.Graph(id='time-domain-chart')
        ], style={'width': '50%', 'display': 'inline-block', 'paddingRight': '10px'}),
        
        html.Div([
            dcc.Graph(id='recovery-scores-chart')
        ], style={'width': '50%', 'display': 'inline-block', 'paddingLeft': '10px'})
    ], style={'marginBottom': '20px'}),
    
    # Frequency Domain & Trend Analysis
    html.Div([
        html.Div([
            dcc.Graph(id='frequency-domain-chart')
        ], style={'width': '50%', 'display': 'inline-block', 'paddingRight': '10px'}),
        
        html.Div([
            dcc.Graph(id='trend-analysis-chart')
        ], style={'width': '50%', 'display': 'inline-block', 'paddingLeft': '10px'})
    ], style={'marginBottom': '20px'}),
    
    # Distribution Analysis
    html.Div([
        dcc.Graph(id='distribution-chart')
    ], style={'marginBottom': '20px'}),
    
    # Detailed Statistics Table
    html.Div([
        html.H3("📊 Detailed Statistics", style={'color': '#2E86AB', 'marginBottom': '15px'}),
        html.Div(id='statistics-table')
    ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '10px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Update every minute
        n_intervals=0,
        disabled=False
    )
], style={'fontFamily': 'Arial, sans-serif', 'margin': '0', 'padding': '20px',
          'backgroundColor': '#f0f2f5'})

# Callback for updating all charts
@app.callback(
    [Output('summary-cards', 'children'),
     Output('time-domain-chart', 'figure'),
     Output('recovery-scores-chart', 'figure'),
     Output('frequency-domain-chart', 'figure'),
     Output('trend-analysis-chart', 'figure'),
     Output('distribution-chart', 'figure'),
     Output('statistics-table', 'children')],
    [Input('days-dropdown', 'value'),
     Input('source-dropdown', 'value'),
     Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(days_back, source_name, n_clicks, n_intervals):
    """Update all dashboard components based on user inputs."""
    try:
        # Get HRV analysis results
        results = hrv_analytics.analyze_hrv_trends(
            days_back=days_back, 
            source_name=source_name,
            include_stats=True
        )
        
        if "error" in results:
            # Return error state
            error_msg = html.Div([
                html.H4("⚠️ No Data Available", style={'color': '#dc3545', 'textAlign': 'center'}),
                html.P(f"Error: {results['error']}", style={'textAlign': 'center'})
            ])
            empty_fig = go.Figure()
            empty_fig.add_annotation(text="No data available", xref="paper", yref="paper",
                                   x=0.5, y=0.5, font_size=16)
            return [error_msg] + [empty_fig] * 5 + [html.Div()]
        
        df = results['dataframe']
        current_values = results['current_values']
        recovery_scores = results['recovery_scores']
        
        # 1. Summary Cards
        summary_cards = create_summary_cards(current_values, recovery_scores, results)
        
        # 2. Time Domain Chart
        time_domain_fig = create_time_domain_chart(df)
        
        # 3. Recovery Scores Chart
        recovery_fig = create_recovery_scores_chart(df)
        
        # 4. Frequency Domain Chart
        frequency_fig = create_frequency_domain_chart(df)
        
        # 5. Trend Analysis Chart
        trend_fig = create_trend_analysis_chart(df)
        
        # 6. Distribution Chart
        distribution_fig = create_distribution_chart(df)
        
        # 7. Statistics Table
        stats_table = create_statistics_table(results.get('statistics', {}))
        
        return [summary_cards, time_domain_fig, recovery_fig, frequency_fig, 
                trend_fig, distribution_fig, stats_table]
        
    except Exception as e:
        error_msg = html.Div([
            html.H4("⚠️ Dashboard Error", style={'color': '#dc3545', 'textAlign': 'center'}),
            html.P(f"Error: {str(e)}", style={'textAlign': 'center'})
        ])
        empty_fig = go.Figure()
        return [error_msg] + [empty_fig] * 5 + [html.Div()]

def create_summary_cards(current_values, recovery_scores, results):
    """Create summary metric cards."""
    cards = html.Div([
        # Current HRV Values
        html.Div([
            html.H4("📈 Current RMSSD", style={'margin': '0', 'color': '#2E86AB'}),
            html.H2(f"{current_values['rmssd']:.1f} ms", style={'margin': '5px 0', 'color': '#333'}),
            html.P("Root Mean Square of Successive Differences", style={'margin': '0', 'fontSize': '12px', 'color': '#666'})
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '10px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                  'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H4("🎯 Simple Recovery", style={'margin': '0', 'color': '#28a745'}),
            html.H2(f"{recovery_scores['simple']:.0f}/100", style={'margin': '5px 0', 'color': '#333'}),
            html.P("Time-domain based score", style={'margin': '0', 'fontSize': '12px', 'color': '#666'})
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '10px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                  'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H4("🔬 Comprehensive", style={'margin': '0', 'color': '#6f42c1'}),
            html.H2(f"{recovery_scores['comprehensive']:.0f}/100", style={'margin': '5px 0', 'color': '#333'}),
            html.P("Full spectrum analysis", style={'margin': '0', 'fontSize': '12px', 'color': '#666'})
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '10px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                  'width': '23%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H4("👤 Personalized", style={'margin': '0', 'color': '#fd7e14'}),
            html.H2(f"{recovery_scores['personalized']:.0f}/100", style={'margin': '5px 0', 'color': '#333'}),
            html.P("Individual baseline score", style={'margin': '0', 'fontSize': '12px', 'color': '#666'})
        ], style={'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '10px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                  'width': '23%', 'display': 'inline-block', 'margin': '1%'})
    ])
    return cards

def create_time_domain_chart(df):
    """Create time domain metrics chart."""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('RMSSD & SDNN Over Time', 'pNN50 Over Time'),
        vertical_spacing=0.15
    )
    
    # RMSSD and SDNN
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['rmssd'], name='RMSSD', 
                  line=dict(color='#2E86AB', width=3), mode='lines+markers'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['sdnn'], name='SDNN', 
                  line=dict(color='#A23B72', width=3), mode='lines+markers'),
        row=1, col=1
    )
    
    # pNN50
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['pnn50'], name='pNN50', 
                  line=dict(color='#F18F01', width=3), mode='lines+markers'),
        row=2, col=1
    )
    
    fig.update_layout(
        title="⏱️ Time Domain HRV Metrics",
        height=500,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="ms", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    
    return fig

def create_recovery_scores_chart(df):
    """Create recovery scores comparison chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['simple_recovery'],
        name='Simple Recovery',
        line=dict(color='#28a745', width=3),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['comprehensive_recovery'],
        name='Comprehensive Recovery',
        line=dict(color='#6f42c1', width=3),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['personalized_recovery'],
        name='Personalized Recovery',
        line=dict(color='#fd7e14', width=3),
        mode='lines+markers'
    ))
    
    # Add reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="green", 
                  annotation_text="Good Recovery (70+)")
    fig.add_hline(y=40, line_dash="dash", line_color="orange", 
                  annotation_text="Moderate Recovery (40+)")
    fig.add_hline(y=20, line_dash="dash", line_color="red", 
                  annotation_text="Poor Recovery (20+)")
    
    fig.update_layout(
        title="🏃‍♂️ Recovery Score Comparison",
        xaxis_title="Date",
        yaxis_title="Recovery Score (0-100)",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_frequency_domain_chart(df):
    """Create frequency domain metrics chart."""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('LF & HF Power', 'LF/HF Ratio'),
        vertical_spacing=0.15
    )
    
    # LF and HF Power
    if 'lf_power' in df.columns and 'hf_power' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['lf_power'], name='LF Power',
                      line=dict(color='#FF6B35', width=3), mode='lines+markers'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['hf_power'], name='HF Power',
                      line=dict(color='#004E89', width=3), mode='lines+markers'),
            row=1, col=1
        )
        
        # Calculate LF/HF ratio
        lf_hf_ratio = df['lf_power'] / df['hf_power'].replace(0, np.nan)
        fig.add_trace(
            go.Scatter(x=df['date'], y=lf_hf_ratio, name='LF/HF Ratio',
                      line=dict(color='#9A031E', width=3), mode='lines+markers'),
            row=2, col=1
        )
    
    fig.update_layout(
        title="📊 Frequency Domain Analysis",
        height=500,
        showlegend=True,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Power (ms²)", row=1, col=1)
    fig.update_yaxes(title_text="Ratio", row=2, col=1)
    
    return fig

def create_trend_analysis_chart(df):
    """Create trend analysis with moving averages."""
    fig = go.Figure()
    
    # Calculate 7-day moving average for RMSSD
    df['rmssd_ma7'] = df['rmssd'].rolling(window=7, min_periods=1).mean()
    df['simple_recovery_ma7'] = df['simple_recovery'].rolling(window=7, min_periods=1).mean()
    
    # RMSSD trend
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['rmssd'],
        name='RMSSD Daily',
        line=dict(color='#2E86AB', width=1),
        opacity=0.3,
        mode='lines'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['rmssd_ma7'],
        name='RMSSD 7-day MA',
        line=dict(color='#2E86AB', width=3),
        mode='lines'
    ))
    
    # Add secondary y-axis for recovery score
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['simple_recovery_ma7'],
        name='Recovery 7-day MA',
        line=dict(color='#28a745', width=3),
        mode='lines',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="📈 Trend Analysis with Moving Averages",
        xaxis_title="Date",
        yaxis_title="RMSSD (ms)",
        yaxis2=dict(
            title="Recovery Score",
            overlaying='y',
            side='right'
        ),
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_distribution_chart(df):
    """Create distribution analysis chart."""
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=('RMSSD Distribution', 'SDNN Distribution', 'pNN50 Distribution',
                       'Simple Recovery', 'Comprehensive Recovery', 'Personalized Recovery'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    metrics = [
        ('rmssd', 'RMSSD', '#2E86AB'),
        ('sdnn', 'SDNN', '#A23B72'),
        ('pnn50', 'pNN50', '#F18F01'),
        ('simple_recovery', 'Simple Recovery', '#28a745'),
        ('comprehensive_recovery', 'Comprehensive Recovery', '#6f42c1'),
        ('personalized_recovery', 'Personalized Recovery', '#fd7e14')
    ]
    
    for i, (metric, name, color) in enumerate(metrics):
        row = 1 if i < 3 else 2
        col = (i % 3) + 1
        
        if metric in df.columns:
            fig.add_trace(
                go.Histogram(x=df[metric], name=name, marker_color=color, 
                           opacity=0.7, nbinsx=15),
                row=row, col=col
            )
    
    fig.update_layout(
        title="📊 HRV Metrics Distribution Analysis",
        height=600,
        showlegend=False
    )
    
    return fig

def create_statistics_table(statistics):
    """Create detailed statistics table."""
    if not statistics:
        return html.P("No statistics available", style={'textAlign': 'center', 'color': '#666'})
    
    table_data = []
    for metric, stats in statistics.items():
        table_data.append(html.Tr([
            html.Td(metric.replace('_', ' ').title(), style={'fontWeight': 'bold'}),
            html.Td(f"{stats['mean']:.2f}"),
            html.Td(f"{stats['std']:.2f}"),
            html.Td(f"{stats['correlation']:.3f}"),
            html.Td(stats['trend_direction'].title()),
            html.Td(stats['trend_strength'].title())
        ]))
    
    table = html.Table([
        html.Thead([
            html.Tr([
                html.Th("Metric"),
                html.Th("Mean"),
                html.Th("Std Dev"),
                html.Th("Correlation"),
                html.Th("Trend Direction"),
                html.Th("Trend Strength")
            ])
        ]),
        html.Tbody(table_data)
    ], style={'width': '100%', 'textAlign': 'center'})
    
    return table

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
