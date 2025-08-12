import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from RunningAnalysis_v50 import RunningAnalysis

# -- Data Load and Scoring Calculation --
@st.cache_data
def get_analysis():
    analysis = RunningAnalysis('g:/My Drive/Phoenix/DataBasesDev/Apex.db')
    # Add advanced metrics if methods exist (per previous instructions)
    if hasattr(analysis, "calculate_recovery_and_readiness"):
        analysis.calculate_recovery_and_readiness()
    if not hasattr(analysis, "weekly_trimp"):
        # Optional fallback to compute weekly_trimp in dashboard if not set in class
        if 'TRIMP' in analysis.training_log.columns and 'date' in analysis.training_log.columns:
            df = analysis.training_log.copy()
            df['date'] = pd.to_datetime(df['date'])
            df['week'] = df['date'].dt.isocalendar().week
            wdf = (
                df.groupby('week')['TRIMP'].sum().reset_index(name='weekly_trimp')
            )
            wdf['acute_load'] = wdf['weekly_trimp'].rolling(window=1).mean()
            wdf['chronic_load'] = wdf['weekly_trimp'].rolling(window=4).mean()
            wdf['acwr'] = wdf['acute_load'] / (wdf['chronic_load'] + 1e-8)
            analysis.weekly_trimp = wdf
    return analysis

analysis = get_analysis()
df = analysis.training_log.copy()

st.title("🏃‍♂️ Running Performance Dashboard")

if df.empty:
    st.warning("No training data loaded.")
    st.stop()

# -- Sidebar Filters --
st.sidebar.header("Session Filters")
min_date = pd.to_datetime(df['date']).min()
max_date = pd.to_datetime(df['date']).max()
date_range = st.sidebar.date_input("Date range", [min_date, max_date])
filtered_df = df[(pd.to_datetime(df['date']) >= pd.to_datetime(date_range[0])) &
                 (pd.to_datetime(df['date']) <= pd.to_datetime(date_range[1]))]

# -- Table of Filtered Sessions --
st.subheader("Training Sessions (Filtered)")
st.dataframe(filtered_df)

# -- Score Selection & Visualization --
score_cols = [c for c in filtered_df.columns if 'score' in c]
default_scores = [x for x in ['recovery_score', 'readiness_score', 'overall_score', 'training_score'] if x in score_cols]
selected_scores = st.sidebar.multiselect(
    "Scores to visualize",
    options=score_cols,
    default=default_scores if default_scores else score_cols[:2]
)

# Plot selected scores over time
if selected_scores:
    fig = px.line(
        filtered_df,
        x='date',
        y=selected_scores,
        labels={'value': 'Score', 'variable': 'Metric', 'date': 'Date'},
        title="Score Trends Over Time"
    )
    st.plotly_chart(fig)

# -- TRIMP and Weekly Load/ACWR Visualizations --
if 'TRIMP' in filtered_df.columns:
    st.subheader("Cardio Training Load (TRIMP)")
    fig2 = px.line(filtered_df, x='date', y='TRIMP', title="TRIMP per Session")
    st.plotly_chart(fig2)
    st.metric("Latest TRIMP", f"{filtered_df['TRIMP'].iloc[-1]:.1f}")

if hasattr(analysis, "weekly_trimp") and isinstance(analysis.weekly_trimp, pd.DataFrame):
    weekly_trimp = analysis.weekly_trimp
    st.subheader("Weekly Training Load & ACWR")
    fig3 = px.line(
        weekly_trimp,
        x='week',
        y=['weekly_trimp','acute_load','chronic_load','acwr'],
        title="Weekly TRIMP, Acute/Chronic Load & ACWR"
    )
    st.plotly_chart(fig3)

# -- General Performance Metrics Trends --
st.subheader("Performance Metric Trends")
perf_cols = ['running_economy', 'vo2max', 'distance', 'efficiency_score', 'heart_rate']
perf_to_plot = [x for x in perf_cols if x in filtered_df.columns]
if perf_to_plot:
    fig4 = px.line(filtered_df, x='date', y=perf_to_plot, title="Key Performance Metrics Over Time")
    st.plotly_chart(fig4)

# -- Radar Chart of Average Normalized Metrics --
if all(x in filtered_df.columns for x in perf_cols):
    st.subheader("Performance Profile Radar")
    norm = lambda x: (x-x.min())/(x.max()-x.min()+1e-6)
    avg_metrics = [norm(filtered_df[x]).mean() for x in perf_cols]
    radar_df = pd.DataFrame(dict(Metric=perf_cols, Value=avg_metrics))
    fig5 = px.line_polar(radar_df, r='Value', theta='Metric', line_close=True,
                         title="Normalized Average Performance Metrics")
    st.plotly_chart(fig5)

# -- KPIs for Recovery/Readiness --
if 'recovery_score' in filtered_df.columns:
    st.metric("Latest Recovery Score", f"{filtered_df['recovery_score'].iloc[-1]:.2f}")
if 'readiness_score' in filtered_df.columns:
    st.metric("Latest Readiness Score", f"{filtered_df['readiness_score'].iloc[-1]:.2f}")

# -- Download Data --
st.sidebar.download_button("Download Data as CSV",
                           data=filtered_df.to_csv(index=False),
                           file_name="filtered_running_data.csv")

st.caption("Dashboard built with Streamlit — aug.2025")
