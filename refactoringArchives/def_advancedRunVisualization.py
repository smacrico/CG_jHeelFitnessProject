'"These visualizations provide:
                #Cumulative distance tracking
                #Moving average of running economy
                #Heart rate vs. pace correlation
                #Training zones distribution
                #Performance progression radar chart
                #Seasonal performance heatmap""



def advanced_visualizations(self):
    """Create advanced performance visualizations"""
    plt.figure(figsize=(20, 15))
    
    # 1. Cumulative Distance Over Time
    plt.subplot(2, 3, 1)
    self.training_log['cumulative_distance'] = self.training_log['distance'].cumsum()
    plt.plot(self.training_log['date'], self.training_log['cumulative_distance'], 'b-o')
    plt.title('Cumulative Running Distance')
    plt.xlabel('Date')
    plt.ylabel('Total Distance (km)')
    plt.xticks(rotation=45)
    
    # 2. Moving Average of Running Economy
    plt.subplot(2, 3, 2)
    self.training_log['running_economy_ma'] = self.training_log['running_economy'].rolling(window=3).mean()
    plt.plot(self.training_log['date'], self.training_log['running_economy'], 'g-', label='Original')
    plt.plot(self.training_log['date'], self.training_log['running_economy_ma'], 'r-', label='3-Session Moving Avg')
    plt.title('Running Economy Trend')
    plt.xlabel('Date')
    plt.ylabel('Running Economy')
    plt.legend()
    plt.xticks(rotation=45)
    
    # 3. Heart Rate vs Pace Correlation
    plt.subplot(2, 3, 3)
    pace = self.training_log['time'] / self.training_log['distance']
    plt.scatter(pace, self.training_log['heart_rate'], alpha=0.7)
    plt.title('Pace vs Heart Rate')
    plt.xlabel('Pace (min/km)')
    plt.ylabel('Heart Rate (bpm)')
    
    # 4. Training Zones Pie Chart
    plt.subplot(2, 3, 4)
    zones = self.training_log.apply(
        lambda row: self.calculate_training_zones(row['running_economy'], row['vo2max']), 
        axis=1
    )
    zone_durations = {zone: len(self.training_log[
        (self.training_log['running_economy'] >= lower) & 
        (self.training_log['running_economy'] < upper)
    ]) for zone, (lower, upper) in zones.iloc[0].items()}
    
    plt.pie(zone_durations.values(), labels=zone_durations.keys(), autopct='%1.1f%%')
    plt.title('Training Zones Distribution')
    
    # 5. Performance Progression Radar Chart
    plt.subplot(2, 3, 5, polar=True)
    metrics = [
        'running_economy', 
        'vo2max', 
        'distance', 
        'efficiency_score', 
        'heart_rate'
    ]
    
    # Normalize metrics
    normalized_metrics = self.training_log[metrics].apply(
        lambda x: (x - x.min()) / (x.max() - x.min())
    )
    
    # Average of normalized metrics for each session
    avg_metrics = normalized_metrics.mean()
    
    # Radar chart
    angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False)
    values = avg_metrics.values
    values = np.concatenate((values, [values[0]]))  # Repeat first value to close the polygon
    angles = np.concatenate((angles, [angles[0]]))  # Repeat first angle
    
    plt.polar(angles, values, 'o-', linewidth=2)
    plt.fill(angles, values, alpha=0.25)
    plt.xticks(angles[:-1], metrics)
    plt.title('Performance Metrics Radar Chart')
    
    # 6. Seasonal Performance Heatmap
    plt.subplot(2, 3, 6)
    self.training_log['month'] = self.training_log['date'].dt.month
    seasonal_performance = self.training_log.groupby('month')['running_economy'].mean()
    
    plt.imshow([seasonal_performance.values], cmap='YlOrRd', aspect='auto')
    plt.colorbar(label='Avg Running Economy')
    plt.title('Seasonal Performance Heatmap')
    plt.xlabel('Month')
    plt.xticks(range(len(seasonal_performance)), seasonal_performance.index)
    
    plt.tight_layout()
    plt.show()

# Add this method to the main method or call it separately
def main():
    # Existing code...
    
    # Call advanced visualizations
    analysis.advanced_visualizations()