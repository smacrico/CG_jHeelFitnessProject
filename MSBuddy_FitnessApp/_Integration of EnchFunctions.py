# Add to your main health analytics script
def enhanced_daily_report_with_visualization():
    """Enhanced daily report with visualizations"""
    
    # Your existing daily report code
    generate_daily_health_report()
    
    # Add HRV visualizations
    visualizer = HRVVisualizer(DB_PATH)
    
    # Create weekly mini-dashboard
    fig = visualizer.create_comprehensive_dashboard(days=7)
    
    # Save visualization for email
    fig.savefig('daily_hrv_dashboard.png', dpi=300, bbox_inches='tight')
    
    # Generate trend insights
    visualizer.generate_trend_report(days=14)
    
    print("Enhanced report with visualizations completed!")
