import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from HRV_dwhAnalytics_v2 import HRVAnalytics

# --- Initialize Analytics ---
hrv = HRVAnalytics("Mercury_DWH-HRV.db")

# --- Sidebar Controls ---
st.sidebar.header("HRV Dashboard Controls")
days = st.sidebar.selectbox("Select period (days)", [7, 14, 30, 60, 90], index=2)
source = st.sidebar.selectbox("HRV Source", ["F3b Monitor+HRV", "Polar H10", "Oura Ring", "All"], index=0)
refresh = st.sidebar.button("Refresh Data")

# --- Load Data ---
results = hrv.analyze_hrv_trends(days_back=days, source_name=source, include_stats=True)
df = results['dataframe']

# --- Summary Metrics ---
st.title("❤️ HRV Analytics Dashboard")
st.markdown("#### Key Metrics")
metrics = results.get('current_values', {})
recovery_scores = results.get('recovery_scores', {})

col1, col2, col3, col4 = st.columns(4)
col1.metric("RMSSD", f"{metrics.get('rmssd', 0):.1f} ms")
col2.metric("Simple Recovery", f"{recovery_scores.get('simple', 0):.0f}/100")
col3.metric("Comprehensive", f"{recovery_scores.get('comprehensive', 0):.0f}/100")
col4.metric("Personalized", f"{recovery_scores.get('personalized', 0):.0f}/100")

# --- Time Domain Plots ---
st.markdown("### Time Domain HRV Metrics")
fig, ax = plt.subplots()
ax.plot(df['date'], df['rmssd'], label='RMSSD', color="blue")
ax.plot(df['date'], df['sdnn'], label='SDNN', color="red")
ax.set_xlabel("Date")
ax.set_ylabel("ms")
ax.legend()
st.pyplot(fig)

# --- Recovery Score Plot ---
st.markdown("### Recovery Scores Over Time")
fig2 = px.line(df, x='date', y=['simple_recovery', 'comprehensive_recovery', 'personalized_recovery'],
               labels={'value': 'Score', 'variable': 'Method'}, title="Recovery Scores")
st.plotly_chart(fig2)

# --- Frequency Domain Plot ---
if 'lf_power' in df.columns and 'hf_power' in df.columns:
    st.markdown("### Frequency Domain Metrics")
    fig3, ax3 = plt.subplots()
    ax3.plot(df['date'], df['lf_power'], label='LF Power', color='orange')
    ax3.plot(df['date'], df['hf_power'], label='HF Power', color='purple')
    ax3.set_xlabel("Date")
    ax3.set_ylabel("ms^2")
    ax3.legend()
    st.pyplot(fig3)

# --- Distribution histogram ---
st.markdown("### Distribution of Simple Recovery Scores")
fig4, ax4 = plt.subplots()
sns.histplot(df['simple_recovery'], bins=15, color='green', kde=True, ax=ax4)
st.pyplot(fig4)

# --- Statistics Table ---
stats = results.get('statistics', {})
if stats:
    st.markdown("### Detailed Trend Statistics")
    stat_table = pd.DataFrame(stats).T
    st.dataframe(stat_table)
else:
    st.info("No trend statistics available for the selected period/source.")

# Auto-refresh functionality can be added with st.experimental_rerun() triggered via a timer or manual input

