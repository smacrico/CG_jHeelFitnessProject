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
