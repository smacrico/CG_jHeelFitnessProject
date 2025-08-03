import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from RunningAnalysis_v50 import RunningAnalysis  # Ensure your class file is named properly and importable

# Load Data
analysis = RunningAnalysis('g:/My Drive/Phoenix/DataBasesDev/Apex.db')
df = analysis.load_training_data()

st.title("🏃‍♂️ Running Performance Dashboard")

# Sidebar filters
st.sidebar.header("Filter Sessions")
min_date = pd.to_datetime(df['date']).min()
max_date = pd.to_datetime(df['date']).max()
date_range = st.sidebar.date_input("Date range", [min_date, max_date])
filtered_df = df[(pd.to_datetime(df['date']) >= pd.to_datetime(date_range[0])) & 
                 (pd.to_datetime(df['date']) <= pd.to_datetime(date_range[1]))]

# Show filtered data
st.subheader("Training Sessions (Filtered)")
st.dataframe(filtered_df)

# TRIMP Visualization Example
if "TRIMP" in filtered_df.columns:
    fig = px.line(filtered_df, x='date', y='TRIMP', title='TRIMP Over Time')
    st.plotly_chart(fig)

# Weekly Load Visualization
if hasattr(analysis, "weekly_trimp"):
    weekly_df = analysis.weekly_trimp
    fig2 = px.line(weekly_df, x='week', y=['weekly_trimp','acute_load','chronic_load','acwr'],
                   title='Weekly Training Load & ACWR')
    st.plotly_chart(fig2)

# More plots: Running Economy Trend
if 'running_economy' in filtered_df.columns:
    fig3 = px.line(filtered_df, x='date', y='running_economy', title='Running Economy Trend')
    st.plotly_chart(fig3)

# Radar chart of normalized metrics (optional, advanced)
metrics = ['running_economy','vo2max','distance','efficiency_score','heart_rate']
if all([m in filtered_df.columns for m in metrics]):
    means = [(filtered_df[m]-filtered_df[m].min())/(filtered_df[m].max()-filtered_df[m].min()+1e-6) for m in metrics]
    means = np.mean(means, axis=1)
    radar_data = pd.DataFrame(dict(r=means, theta=metrics))
    fig4 = px.line_polar(radar_data, r='r', theta='theta', line_close=True, title='Performance Radar')
    st.plotly_chart(fig4)
 