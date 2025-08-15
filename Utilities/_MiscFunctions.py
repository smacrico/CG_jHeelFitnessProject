def calculate_recovery_score(activity_id, conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT armssd, asdnn, nn50 FROM hrv_sessions WHERE name is 'F3b Monitor+HRV' AND activity_id = ?
    """, (activity_id,))
    result = cursor.fetchone()
    if result and all(result):
        rmssd_score = min(100, result[0] / 2)
        sdnn_score = min(100, result[1] / 2)
        pnn50_score = result[2] or 0
        recovery_score = (rmssd_score + sdnn_score + pnn50_score) / 3
        return recovery_score
    else:
        return None
    

def analyze_hrv_trends(days=30):
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(armssd) as avg_rmssd, AVG(asdnn) as avg_sdnn
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) and name is 'F3b Monitor+HRV'
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    if df.empty:
        print("No HRV data found for analysis.")
        return
    print(df)
    # Trend calculation (simple linear regression)
    if len(df) > 1:
        x = np.arange(len(df))
        rmssd_trend = np.polyfit(x, df['avg_rmssd'], 1)[0]
        print(f"RMSSD trend (per day): {rmssd_trend:.2f}")
    else:
        print("Not enough data for trend analysis.")


*********************************************************************************************
************************************ results of Scripts *************************************
*********************************************************************************************

###################################### HRV_datawarehouse.py ********************************
=== HRV Health Monitoring Report ===
Generated: 2025-08-14 18:03:51

Warning: Only 4 days of data available. Need at least 14 days for reliable baseline.

--- Recent HRV Drops ---
No baseline or recent data available for drop detection.
    


###################################### HRV_Analysis_V1.0.py ********************************

=== HRV TREND ANALYSIS REPORT ===
Period: 2025-07-15 to 2025-08-14 (31 days)
RMSSD: improving (weak), slope=0.100, correlation=0.202
SDNN: improving (negligible), slope=0.100, correlation=0.122
RMSSD recent change: +1.4%
SDNN recent change: +7.5%
{'activity_id': '17080654324', 'name': 'F3b Monitor+HRV', 'method': 'simple', 'recovery_score': 15.758150736490885} None None

###################################### HRV_datawarehouse_V1.5.py ********************************

Plotting HRV trend and histogram...
Fetching daily HRV data for the last 30 days...
=== HRV TREND ANALYSIS ===
RMSSD Trend: [ 0.09997902 34.19213834]
RMSSD Correlation: 0.202
SDNN Trend: [ 0.09958312 53.3661335 ]
SDNN Correlation: 0.122

============================================================
HRV TREND ANALYSIS REPORT
============================================================
Analysis Period: 2025-07-15 to 2025-08-14
Data Points: 31 days

[Trend] TREND SUMMARY:
------------------------------
RMSSD: IMPROVING (weak)
  Slope: +0.100 ms/day
  Correlation: 0.202
SDNN: IMPROVING (negligible)
  Slope: +0.100 ms/day
  Correlation: 0.122

[Trend] TREND OVERALL:
------------------------------
RMSSD: +1.4% change
SDNN: +7.5% change
============================================================

=== RECOVERY SCORE CALCULATIONS ===
Simple Recovery Score for 17080654324 (F3b Monitor+HRV): 15.8/100

*************************************************************
###################################### HRV_datawarehouse V1.9.py ********************************

Calculating recovery score for activity 20054944628...
Recovery score for 20054944628: 16.90004316965739
    
    
          date  avg_rmssd   avg_sdnn
0   2025-08-14  41.193202  54.578088
1   2025-08-13  31.104756  47.992107
2   2025-08-12  29.773281  56.608985
3   2025-08-11  33.556938  57.458425
4   2025-08-10  41.709774  56.154129
5   2025-08-09  37.237118  62.925349
6   2025-08-08  38.643154  76.930269
7   2025-08-07  45.697351  56.281250
8   2025-08-06  38.368884  63.002989
9   2025-08-05  40.049782  52.052590
10  2025-08-04  34.628835  50.898397
11  2025-08-03  34.031482  49.860899
12  2025-08-02  32.561503  57.904910
13  2025-08-01  30.459620  42.065074
14  2025-07-31  30.063349  43.474328
15  2025-07-30  40.094465  48.811297
16  2025-07-29  39.860921  56.829896
17  2025-07-28  35.436429  53.734973
18  2025-07-27  33.074940  53.179422
19  2025-07-26  35.321335  50.749350
20  2025-07-25  33.074123  61.952751
21  2025-07-24  33.361120  46.202230
22  2025-07-23  37.653577  58.730669
23  2025-07-22  43.311150  52.552341
24  2025-07-21  39.864658  60.965094
25  2025-07-20  29.772264  53.306842
26  2025-07-19  38.940332  65.017590
27  2025-07-18  29.092544  55.351542
28  2025-07-17  29.789294  51.346379
29  2025-07-16  32.353850  62.911921
30  2025-07-15  36.366503  40.826202
RMSSD trend (per day): -0.10
=== HRV Health Monitoring Report ===
Generated: 2025-08-14 18:21:13

Establishing baseline over the last 14 days...
Baseline established over 15 days:
RMSSD: 35.9 ± 4.9
Normal range: 31.8 - 39.3

--- Recent HRV Drops ---
Detecting HRV drops over the last 14 days...



