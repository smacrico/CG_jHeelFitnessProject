<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

## Power BI HRV Analytics Dashboard with Predictive Capabilities

Excellent idea! Power BI is perfect for creating sophisticated HRV analytics dashboards with predictive capabilities. Here's a comprehensive guide to take your HRV analytics to the next level:

### 1. Data Connection \& Model Setup

#### Database Connection Options

**Option A: Direct SQLite Connection**

```sql
-- Power BI M Query for SQLite connection
let
    Source = Sqlite.Database(File.Contents("c:\smakryko\myHealthData\DataBasesDev\Mercury_DWH-HRV.db")),
    hrv_sessions = Source{[Schema="main",Item="hrv_sessions"]}[Data],
    hrv_records = Source{[Schema="main",Item="hrv_records"]}[Data]
in
    hrv_sessions
```

**Option B: Python Data Pipeline (Recommended)**

```python
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def export_hrv_data_for_powerbi():
    """Export HRV data in Power BI optimized format"""
    
    conn = sqlite3.connect("c:/smakryko/myHealthData/DataBasesDev/Mercury_DWH-HRV.db")
    
    # Enhanced sessions query with calculated fields
    sessions_query = """
    SELECT 
        activity_id,
        name,
        source,
        datetime(timestamp) as session_datetime,
        date(timestamp) as session_date,
        strftime('%Y', timestamp) as year,
        strftime('%m', timestamp) as month,
        strftime('%W', timestamp) as week_number,
        strftime('%w', timestamp) as day_of_week,
        strftime('%H', timestamp) as hour,
        sport,
        duration_seconds,
        hrv_rmssd,
        sdnn,
        hrv_pnn50,
        mean_hr,
        recovery,
        lf,
        hf,
        vlf,
        CASE WHEN hf > 0 THEN lf/hf ELSE NULL END as lf_hf_ratio,
        stress_hrpa,
        
        -- Recovery categories
        CASE 
            WHEN recovery >= 80 THEN 'Excellent'
            WHEN recovery >= 70 THEN 'Good'
            WHEN recovery >= 60 THEN 'Moderate'
            WHEN recovery >= 50 THEN 'Poor'
            ELSE 'Very Poor'
        END as recovery_category,
        
        -- HRV health zones
        CASE 
            WHEN hrv_rmssd >= 50 THEN 'Optimal'
            WHEN hrv_rmssd >= 35 THEN 'Good'
            WHEN hrv_rmssd >= 25 THEN 'Fair'
            ELSE 'Poor'
        END as hrv_zone,
        
        -- Trend indicators (7-day rolling average)
        AVG(hrv_rmssd) OVER (
            ORDER BY timestamp 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as rmssd_7day_avg,
        
        AVG(recovery) OVER (
            ORDER BY timestamp 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as recovery_7day_avg
        
    FROM hrv_sessions
    WHERE timestamp >= date('now', '-365 days')
    ORDER BY timestamp DESC
    """
    
    # Export to CSV for Power BI import
    df_sessions = pd.read_sql_query(sessions_query, conn)
    df_sessions.to_csv("hrv_sessions_powerbi.csv", index=False)
    
    # Create time dimension table
    date_range = pd.date_range(
        start=(datetime.now() - timedelta(days=365)).date(),
        end=datetime.now().date(),
        freq='D'
    )
    
    date_dim = pd.DataFrame({
        'Date': date_range,
        'Year': date_range.year,
        'Month': date_range.month,
        'MonthName': date_range.strftime('%B'),
        'Week': date_range.isocalendar().week,
        'DayOfWeek': date_range.dayofweek,
        'DayName': date_range.strftime('%A'),
        'Quarter': date_range.quarter,
        'IsWeekend': date_range.dayofweek >= 5
    })
    
    date_dim.to_csv("date_dimension.csv", index=False)
    
    # Create targets/baselines table
    targets = pd.DataFrame({
        'Metric': ['RMSSD', 'SDNN', 'Recovery', 'Mean_HR', 'HF_Power'],
        'Target_Value': [45, 50, 75, 65, 500],
        'Optimal_Min': [50, 60, 80, 60, 600],
        'Warning_Threshold': [30, 35, 60, 75, 300],
        'Critical_Threshold': [20, 25, 50, 85, 200]
    })
    


    targets.to_csv("hrv_targets.csv", index=False)
    
    conn.close()
    print("Data exported for Power BI import")

# Run the export
export_hrv_data_for_powerbi()
```


### 2. Power BI Data Model Design

#### Recommended Table Structure

**Fact Tables:**

- `HRV_Sessions` (main fact table)
- `HRV_Records` (detailed beat-by-beat data)

**Dimension Tables:**

- `Date_Dimension` (comprehensive date hierarchy)
- `HRV_Targets` (personal baselines and targets)
- `Activity_Types` (sport/activity categories)


#### Key DAX Measures

```dax
-- === BASIC HRV MEASURES ===

-- Average RMSSD
Avg_RMSSD = AVERAGE(HRV_Sessions[hrv_rmssd])

-- RMSSD Trend (30-day)
RMSSD_Trend_30d = 
VAR CurrentDate = MAX(Date_Dimension[Date])
VAR PreviousPeriod = DATEADD(Date_Dimension[Date], -30, DAY)
VAR CurrentAvg = CALCULATE([Avg_RMSSD], Date_Dimension[Date] > PreviousPeriod)
VAR PreviousAvg = CALCULATE([Avg_RMSSD], 
    Date_Dimension[Date] <= PreviousPeriod && 
    Date_Dimension[Date] > DATEADD(PreviousPeriod, -30, DAY))
RETURN 
IF(PreviousAvg <> 0, (CurrentAvg - PreviousAvg) / PreviousAvg, BLANK())

-- === RECOVERY SCORING ===

-- Comprehensive Recovery Score
Recovery_Score_Comprehensive = 
VAR RMSSD_Score = MIN(100, MAX(0, [Avg_RMSSD] / 0.8))
VAR SDNN_Score = MIN(100, MAX(0, AVERAGE(HRV_Sessions[sdnn]) / 1.0))
VAR HF_Score = 
    IF(AVERAGE(HRV_Sessions[hf]) > 0,
       MIN(100, MAX(0, LOG10(AVERAGE(HRV_Sessions[hf])) * 25)),
       50)
VAR HR_Score = MIN(100, MAX(0, 100 - ABS(AVERAGE(HRV_Sessions[mean_hr]) - 60) * 2))
RETURN (RMSSD_Score * 0.4 + SDNN_Score * 0.3 + HF_Score * 0.2 + HR_Score * 0.1)

-- === TREND ANALYSIS ===

-- HRV Trend Direction
HRV_Trend_Direction = 
VAR TrendValue = [RMSSD_Trend_30d]
RETURN 
SWITCH(TRUE(),
    TrendValue > 0.05, "↗️ Improving",
    TrendValue < -0.05, "↘️ Declining", 
    "➡️ Stable")

-- === RISK INDICATORS ===

-- Flare Risk Score (MS-specific)
MS_Flare_Risk = 
VAR HRV_Risk = 
    IF([RMSSD_Trend_30d] < -0.15, 0.3, 
    IF([RMSSD_Trend_30d] < -0.1, 0.15, 0))
VAR Recovery_Risk = 
    IF(AVERAGE(HRV_Sessions[recovery]) < 60, 0.25, 
    IF(AVERAGE(HRV_Sessions[recovery]) < 70, 0.1, 0))
VAR Stress_Risk = 
    IF(AVERAGE(HRV_Sessions[stress_hrpa]) > 50, 0.2, 
    IF(AVERAGE(HRV_Sessions[stress_hrpa]) > 35, 0.1, 0))
VAR Variability_Risk = 
    IF(STDEV.P(HRV_Sessions[hrv_rmssd]) / [Avg_RMSSD] > 0.3, 0.25, 0)
RETURN (HRV_Risk + Recovery_Risk + Stress_Risk + Variability_Risk) * 100

-- Risk Level Category
Risk_Level = 
VAR RiskScore = [MS_Flare_Risk]
RETURN 
SWITCH(TRUE(),
    RiskScore >= 70, "🔴 Critical",
    RiskScore >= 50, "🟠 High",
    RiskScore >= 30, "🟡 Moderate",
    "🟢 Low")

-- === PREDICTIVE MEASURES ===

-- Next Week Recovery Prediction (Simple Linear)
Predicted_Recovery_Next_Week = 
VAR CurrentTrend = [RMSSD_Trend_30d]
VAR CurrentRecovery = AVERAGE(HRV_Sessions[recovery])
VAR PredictedChange = CurrentTrend * 7 * 1.2  -- 7 days * conversion factor
RETURN 
MIN(100, MAX(0, CurrentRecovery + PredictedChange))

-- HRV Stability Index
HRV_Stability_Index = 
VAR CV_RMSSD = DIVIDE(STDEV.P(HRV_Sessions[hrv_rmssd]), [Avg_RMSSD])
VAR CV_Recovery = DIVIDE(STDEV.P(HRV_Sessions[recovery]), AVERAGE(HRV_Sessions[recovery]))
RETURN 
MAX(0, 100 - (CV_RMSSD + CV_Recovery) * 100)
```


### 3. Dashboard Layout Design

#### Page 1: Executive Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    HRV HEALTH DASHBOARD                        │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Current Status        │ 📈 7-Day Trend    │ ⚠️ Risk Level   │
│ Recovery: 78/100         │ RMSSD: ↗️ +3.2%   │ 🟡 Moderate     │
│ HRV Score: 85/100        │ Recovery: ↗️ +1.8% │ Next Review: 3d  │
│ Last Session: 2h ago     │ Stability: 92%     │ Flare Risk: 32% │
├─────────────────────────────────────────────────────────────────┤
│           📉 30-DAY HRV TRENDS                                  │
│  [Line Chart: RMSSD, SDNN, Recovery over time with trendlines] │
├─────────────────────────────────────────────────────────────────┤
│ 🎯 Goals vs Actual      │ 📅 Weekly Pattern │ 🔮 Predictions   │
│ [Gauge Charts]          │ [Heatmap by day]   │ [Forecast chart] │
└─────────────────────────────────────────────────────────────────┘
```


#### Page 2: Detailed Analytics

```
┌─────────────────────────────────────────────────────────────────┐
│                    DETAILED HRV ANALYSIS                       │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Frequency Domain     │ ⏱️ Time Domain     │ 💓 Heart Rate    │
│ [LF/HF Ratio Chart]     │ [RMSSD/SDNN Chart] │ [HR Variability] │
├─────────────────────────────────────────────────────────────────┤
│           🔍 CORRELATION ANALYSIS                              │
│  [Scatter plots: HRV vs Sleep, Stress, Activity, Weather]      │
├─────────────────────────────────────────────────────────────────┤
│ 📈 Statistical Summary  │ 🎯 Personal Zones  │ 📊 Distribution  │
│ [Table with stats]      │ [Zone performance]  │ [Histograms]     │
└─────────────────────────────────────────────────────────────────┘
```


#### Page 3: Predictive Analytics

```
┌─────────────────────────────────────────────────────────────────┐
│                    PREDICTIVE ANALYTICS                        │
├─────────────────────────────────────────────────────────────────┤
│ 🔮 7-Day Forecast       │ ⚠️ Risk Prediction │ 🎯 Recommendations│
│ [Forecast line chart]   │ [Risk gauge/meter] │ [Action items]    │
├─────────────────────────────────────────────────────────────────┤
│           📊 PATTERN RECOGNITION                               │
│  [Seasonal patterns, Weekly cycles, Monthly trends]            │
├─────────────────────────────────────────────────────────────────┤
│ 🧠 ML Insights         │ 📈 Trend Confidence│ 🎲 Scenarios     │
│ [Key factor analysis]   │ [Prediction bands] │ [What-if analysis]│
└─────────────────────────────────────────────────────────────────┘
```


### 4. Advanced Predictive Analytics

#### Using Power BI's AI Features

**1. Key Influencers Visual**

```dax
-- Create binary outcome for Key Influencers
High_Recovery_Day = IF(HRV_Sessions[recovery] > 75, "High Recovery", "Low Recovery")
```

**2. Decomposition Tree**

```dax
-- Factors affecting HRV decline
HRV_Decline_Event = 
IF([RMSSD_Trend_30d] < -0.1, "HRV Declined", "HRV Stable/Improved")
```

**3. Smart Narrative**

- Add Smart Narrative visual to automatically generate insights about HRV trends


#### Custom R/Python Visuals for Advanced Predictions

**R Script for ARIMA Forecasting:**

```r
# Power BI R Visual Script
library(forecast)
library(ggplot2)

# Get data from Power BI
hrv_data <- dataset$hrv_rmssd
dates <- as.Date(dataset$session_date)

# Create time series
ts_data <- ts(hrv_data, frequency = 7)  # Weekly seasonality

# Fit ARIMA model
arima_model <- auto.arima(ts_data)

# Generate forecast
forecast_result <- forecast(arima_model, h = 14)  # 14-day forecast

# Plot
autoplot(forecast_result) +
  ggtitle("HRV RMSSD 14-Day Forecast") +
  xlab("Time") +
  ylab("RMSSD (ms)") +
  theme_minimal()
```

**Python Script for ML Predictions:**

```python
# Power BI Python Visual Script
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

# Get data from Power BI
df = dataset.copy()

# Feature engineering
df['day_of_week'] = pd.to_datetime(df['session_date']).dt.dayofweek
df['hour'] = pd.to_datetime(df['session_datetime']).dt.hour
df['rmssd_lag1'] = df['hrv_rmssd'].shift(1)
df['rmssd_lag7'] = df['hrv_rmssd'].shift(7)

# Prepare features
features = ['day_of_week', 'hour', 'mean_hr', 'stress_hrpa', 'rmssd_lag1', 'rmssd_lag7']
X = df[features].dropna()
y = df['hrv_rmssd'].iloc[len(df)-len(X):]

# Train model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, y)

# Predict next value
next_prediction = rf_model.predict(X.tail(1))[0]

# Feature importance plot
importance = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

plt.figure(figsize=(10, 6))
plt.barh(importance['feature'], importance['importance'])
plt.title('HRV Prediction - Feature Importance')
plt.xlabel('Importance')
plt.show()
```


### 5. Real-Time Integration

#### Automated Data Refresh

```python
# Scheduled Python script for data refresh
import schedule
import time

def update_powerbi_data():
    """Update Power BI data source"""
    # Export fresh data
    export_hrv_data_for_powerbi()
    
    # Trigger Power BI refresh (using REST API)
    import requests
    
    # Power BI REST API call
    headers = {'Authorization': f'Bearer {access_token}'}
    refresh_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes"
    
    response = requests.post(refresh_url, headers=headers)
    print(f"Power BI refresh triggered: {response.status_code}")

# Schedule updates
schedule.every(4).hours.do(update_powerbi_data)
schedule.every().day.at("06:00").do(update_powerbi_data)

while True:
    schedule.run_pending()
    time.sleep(300)  # Check every 5 minutes
```


### 6. Mobile Optimization

#### Mobile Dashboard Layout

- Focus on key metrics (Recovery Score, Risk Level, Trend)
- Use large, touch-friendly visuals
- Implement drill-through for detailed analysis
- Add bookmarks for quick navigation


### 7. Alert System

#### Power BI Alerts Configuration

```dax
-- Alert conditions
Critical_HRV_Alert = 
IF([MS_Flare_Risk] > 70 || [Avg_RMSSD] < 25, "ALERT", "OK")

Recovery_Alert = 
IF([Recovery_Score_Comprehensive] < 50, "LOW_RECOVERY", "OK")
```


### 8. Implementation Steps

1. **Phase 1: Basic Dashboard**
    - Set up data connection
    - Create core visualizations
    - Implement basic DAX measures
2. **Phase 2: Advanced Analytics**
    - Add predictive models
    - Implement AI visuals
    - Create automated insights
3. **Phase 3: Integration \& Automation**
    - Set up automated refresh
    - Configure alerts
    - Optimize for mobile
4. **Phase 4: ML Enhancement**
    - Implement custom R/Python visuals
    - Add advanced forecasting
    - Create personalized recommendations

This Power BI solution will transform your HRV data into actionable insights with predictive capabilities specifically tailored for MS health management. The dashboard will provide both immediate health status visibility and forward-looking analytics to help prevent flares and optimize recovery strategies.

