# Add this to your unified HRV warehouse script
def analyze_session_hrv_detailed(activity_id):
    """Enhanced HRV analysis for a specific session"""
    conn = sqlite3.connect(DB_PATH)
    
    # Get IBI data from records
    query = """
    SELECT RRint FROM hrv_records 
    WHERE activity_id = ? AND RRint IS NOT NULL 
    ORDER BY record
    """
    ibi_data = pd.read_sql_query(query, conn, params=(activity_id,))['RRint'].values
    conn.close()
    
    if len(ibi_data) < 10:
        return None
    
    # Run enhanced analysis
    ibi_filtered, _ = filter_ibi_artifacts(ibi_data, method='statistical')
    time_metrics = calculate_time_domain_hrv(ibi_filtered)
    freq_metrics = calculate_frequency_domain_hrv(ibi_filtered)
    hrv_score = calculate_enhanced_hrv_score(time_metrics, freq_metrics)
    
    return {
        'time_domain': time_metrics,
        'frequency_domain': freq_metrics,
        'hrv_score': hrv_score
    }
