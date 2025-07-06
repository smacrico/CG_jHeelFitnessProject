# --- Enhanced HRV Pattern Detection ---
def establish_baseline(days=21):
    """Establish personal HRV baseline over specified days"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd, 
           AVG(sdnn) as avg_sdnn, AVG(hrv_pnn50) as avg_pnn50
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if len(df) < 14:
        print(f"Warning: Only {len(df)} days of data available. Need at least 14 days for reliable baseline.")
        return None
    
    baseline = {
        'rmssd_mean': df['avg_rmssd'].mean(),
        'rmssd_std': df['avg_rmssd'].std(),
        'rmssd_lower': df['avg_rmssd'].quantile(0.25),
        'rmssd_upper': df['avg_rmssd'].quantile(0.75),
        'sdnn_mean': df['avg_sdnn'].mean(),
        'sdnn_std': df['avg_sdnn'].std(),
        'days_calculated': len(df)
    }
    
    print(f"Baseline established over {baseline['days_calculated']} days:")
    print(f"RMSSD: {baseline['rmssd_mean']:.1f} ± {baseline['rmssd_std']:.1f}")
    print(f"Normal range: {baseline['rmssd_lower']:.1f} - {baseline['rmssd_upper']:.1f}")
    
    return baseline

def detect_hrv_drops(baseline, days=7, drop_threshold=0.7):
    """Detect sudden HRV drops below baseline"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd,
           AVG(sdnn) as avg_sdnn, COUNT(*) as readings
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if baseline is None or df.empty:
        print("No baseline or recent data available for drop detection.")
        return []
    
    alerts = []
    threshold = baseline['rmssd_lower'] * drop_threshold
    
    for _, row in df.iterrows():
        if row['avg_rmssd'] < threshold:
            severity = "SEVERE" if row['avg_rmssd'] < (baseline['rmssd_mean'] * 0.6) else "MODERATE"
            alerts.append({
                'date': row['date'],
                'rmssd': row['avg_rmssd'],
                'severity': severity,
                'drop_percent': ((baseline['rmssd_mean'] - row['avg_rmssd']) / baseline['rmssd_mean']) * 100
            })
    
    return alerts

def detect_sustained_low_hrv(baseline, days=14, consecutive_days=3):
    """Detect sustained low HRV periods"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) ASC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if baseline is None or len(df) < consecutive_days:
        return []
    
    threshold = baseline['rmssd_lower']
    sustained_periods = []
    current_period = []
    
    for _, row in df.iterrows():
        if row['avg_rmssd'] < threshold:
            current_period.append(row)
        else:
            if len(current_period) >= consecutive_days:
                sustained_periods.append({
                    'start_date': current_period[0]['date'],
                    'end_date': current_period[-1]['date'],
                    'duration_days': len(current_period),
                    'avg_rmssd': np.mean([r['avg_rmssd'] for r in current_period])
                })
            current_period = []
    
    # Check if current period is still ongoing
    if len(current_period) >= consecutive_days:
        sustained_periods.append({
            'start_date': current_period[0]['date'],
            'end_date': current_period[-1]['date'],
            'duration_days': len(current_period),
            'avg_rmssd': np.mean([r['avg_rmssd'] for r in current_period]),
            'ongoing': True
        })
    
    return sustained_periods

def calculate_hrv_7day_average():
    """Calculate rolling 7-day HRV average"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as daily_rmssd
    FROM hrv_sessions
    WHERE timestamp >= date('now', '-30 days') AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) < 7:
        print("Not enough data for 7-day average calculation.")
        return None
    
    df['rolling_7day'] = df['daily_rmssd'].rolling(window=7, min_periods=4).mean()
    df['trend_direction'] = df['rolling_7day'].diff()
    
    return df

def detect_erratic_patterns(days=14):
    """Detect erratic HRV patterns (high variability)"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT date(timestamp) as date, AVG(hrv_rmssd) as avg_rmssd,
           STDEV(hrv_rmssd) as std_rmssd, COUNT(*) as readings
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) AND hrv_rmssd IS NOT NULL
    GROUP BY date(timestamp)
    HAVING COUNT(*) > 1
    ORDER BY date(timestamp) DESC
    """
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    
    if df.empty:
        return []
    
    # Calculate coefficient of variation for each day
    df['cv'] = df['std_rmssd'] / df['avg_rmssd']
    high_variability_threshold = df['cv'].quantile(0.8)  # Top 20% most variable days
    
    erratic_days = df[df['cv'] > high_variability_threshold].copy()
    
    return erratic_days[['date', 'avg_rmssd', 'std_rmssd', 'cv']].to_dict('records')

def comprehensive_hrv_health_check():
    """Run comprehensive HRV health monitoring"""
    print("=== HRV Health Monitoring Report ===")
    print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Establish baseline
    baseline = establish_baseline(days=21)
    print()
    
    # Check for recent drops
    print("--- Recent HRV Drops ---")
    drops = detect_hrv_drops(baseline, days=7)
    if drops:
        for drop in drops:
            print(f"⚠️  {drop['date']}: RMSSD {drop['rmssd']:.1f} ({drop['severity']} - {drop['drop_percent']:.1f}% below baseline)")
    else:
        print("✅ No significant HRV drops detected in the last 7 days.")
    print()
    
    # Check for sustained low periods
    print("--- Sustained Low HRV Periods ---")
    sustained = detect_sustained_low_hrv(baseline, days=14)
    if sustained:
        for period in sustained:
            ongoing = " (ONGOING)" if period.get('ongoing') else ""
            print(f"🔴 {period['start_date']} to {period['end_date']}: {period['duration_days']} days{ongoing}")
    else:
        print("✅ No sustained low HRV periods detected.")
    print()
    
    # Check for erratic patterns
    print("--- Erratic HRV Patterns ---")
    erratic = detect_erratic_patterns(days=14)
    if erratic:
        for day in erratic:
            print(f"📊 {day['date']}: High variability (CV: {day['cv']:.2f})")
    else:
        print("✅ No erratic HRV patterns detected.")
    print()
    
    # 7-day trend
    print("--- 7-Day HRV Trend ---")
    trend_df = calculate_hrv_7day_average()
    if trend_df is not None and len(trend_df) >= 7:
        latest_avg = trend_df.iloc[0]['rolling_7day']
        trend_direction = trend_df.iloc[0]['trend_direction']
        if baseline:
            vs_baseline = ((latest_avg - baseline['rmssd_mean']) / baseline['rmssd_mean']) * 100
            print(f"Current 7-day average: {latest_avg:.1f} ({vs_baseline:+.1f}% vs baseline)")
        else:
            print(f"Current 7-day average: {latest_avg:.1f}")
        
        if trend_direction > 0:
            print("📈 Trend: Improving")
        elif trend_direction < 0:
            print("📉 Trend: Declining")
        else:
            print("➡️ Trend: Stable")
    else:
        print("Insufficient data for trend analysis.")
    print()
    
    # Health status summary
    print("--- Health Status Summary ---")
    risk_factors = 0
    if drops:
        risk_factors += len(drops)
    if sustained:
        risk_factors += len(sustained) * 2  # Weight sustained periods more heavily
    if erratic:
        risk_factors += len(erratic)
    
    if risk_factors == 0:
        print("✅ LOW RISK: HRV patterns appear normal")
    elif risk_factors <= 2:
        print("⚠️  MODERATE RISK: Some concerning patterns detected")
    else:
        print("🔴 HIGH RISK: Multiple concerning patterns detected")
    
    print(f"Risk factors detected: {risk_factors}")
    print("=== End Report ===")

# --- Updated Main Execution ---
if __name__ == "__main__":
    create_unified_tables()
    # Example: ingest all .fit files from a folder
    ingest_folder("C:/smakryko/myHealthData/HealtDataSystemAnalysis/TestFitFiles/Garmin", source_hint="GARMIN")
    
    # Run comprehensive health check
    comprehensive_hrv_health_check()
