# Add these imports to the existing ones
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from scipy.stats import pearsonr
import calendar

class AdvancedHRVAnalysis(EnhancedHRVAnalysis):
    def __init__(self):
        super().__init__()
        
    def calculate_statistics(self):
        """Calculate advanced statistical metrics"""
        stats_dict = {
            'Weekly Stats': self.hrv_log.resample('W', on='date').agg({
                'sdnn': ['mean', 'std', 'min', 'max'],
                'rmssd': ['mean', 'std', 'min', 'max'],
                'lf_hf_ratio': ['mean', 'std']
            }),
            'Monthly Trends': self.hrv_log.resample('M', on='date').mean(),
            'Correlations': self.calculate_correlations(),
            'Variability Index': self.calculate_variability_index()
        }
        return stats_dict
    
    def calculate_correlations(self):
        """Calculate correlations between different HRV metrics"""
        correlation_metrics = ['sdnn', 'rmssd', 'lf_hf_ratio', 'mean_hr']
        corr_matrix = self.hrv_log[correlation_metrics].corr()
        return corr_matrix
    
    def calculate_variability_index(self):
        """Calculate custom variability index"""
        scaled_data = StandardScaler().fit_transform(
            self.hrv_log[['sdnn', 'rmssd', 'lf_hf_ratio']])
        return np.mean(scaled_data, axis=1)

    def visualize_advanced_metrics(self):
        """Generate advanced visualization plots"""
        plt.style.use('seaborn')
        
        # Create subplots
        fig = plt.figure(figsize=(20, 25))
        
        # 1. Time Series Decomposition
        self._plot_time_series_decomposition(plt.subplot(5, 2, 1))
        
        # 2. Weekly Patterns
        self._plot_weekly_patterns(plt.subplot(5, 2, 2))
        
        # 3. Correlation Heatmap
        self._plot_correlation_heatmap(plt.subplot(5, 2, 3))
        
        # 4. Distribution Analysis
        self._plot_distribution_analysis(plt.subplot(5, 2, 4))
        
        # 5. Training Load Impact
        self._plot_training_load_impact(plt.subplot(5, 2, 5))
        
        # 6. Recovery Pattern Analysis
        self._plot_recovery_patterns(plt.subplot(5, 2, 6))
        
        # 7. Circadian Rhythm Analysis
        self._plot_circadian_rhythm(plt.subplot(5, 2, 7))
        
        # 8. Stress Response Analysis
        self._plot_stress_response(plt.subplot(5, 2, 8))
        
        # 9. Long-term Trends
        self._plot_long_term_trends(plt.subplot(5, 2, 9))
        
        # 10. Autonomic Balance Dashboard
        self._plot_autonomic_dashboard(plt.subplot(5, 2, 10))
        
        plt.tight_layout()
        plt.show()

    def _plot_time_series_decomposition(self, ax):
        """Plot time series decomposition of HRV metrics"""
        decomposition = seasonal_decompose(
            self.hrv_log['sdnn'].values, 
            period=7,  # Weekly seasonality
            extrapolate_trend='freq'
        )
        
        ax.plot(decomposition.trend, label='Trend')
        ax.plot(decomposition.seasonal, label='Seasonal')
        ax.plot(decomposition.resid, label='Residual')
        ax.set_title('HRV Time Series Decomposition')
        ax.legend()

    def _plot_weekly_patterns(self, ax):
        """Plot weekly patterns in HRV metrics"""
        weekly_avg = self.hrv_log.groupby(
            self.hrv_log['date'].dt.dayofweek
        )['sdnn'].mean()
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        ax.bar(days, weekly_avg)
        ax.set_title('Weekly HRV Patterns')
        ax.set_ylabel('Average SDNN (ms)')

    def _plot_correlation_heatmap(self, ax):
        """Plot correlation heatmap of HRV metrics"""
        corr_matrix = self.calculate_correlations()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
        ax.set_title('HRV Metrics Correlation Heatmap')

    def _plot_distribution_analysis(self, ax):
        """Plot distribution analysis of HRV metrics"""
        metrics = ['sdnn', 'rmssd', 'lf_hf_ratio']
        for metric in metrics:
            sns.kdeplot(data=self.hrv_log[metric], label=metric, ax=ax)
        ax.set_title('HRV Metrics Distribution')
        ax.legend()

    def _plot_training_load_impact(self, ax):
        """Plot training load impact on HRV"""
        # Assuming training load is calculated from intensity and duration
        training_load = self.hrv_log['mean_hr'] * self.hrv_log['sdnn']
        ax.scatter(training_load, self.hrv_log['rmssd'])
        ax.set_title('Training Load vs HRV')
        ax.set_xlabel('Training Load (arbitrary units)')
        ax.set_ylabel('RMSSD (ms)')

    def _plot_recovery_patterns(self, ax):
        """Plot recovery patterns"""
        recovery_metric = self.hrv_log['rmssd'].rolling(window=7).mean()
        ax.plot(self.hrv_log['date'], recovery_metric)
        ax.set_title('7-Day Rolling Average Recovery Pattern')
        ax.set_ylabel('RMSSD (ms)')

    def _plot_circadian_rhythm(self, ax):
        """Plot circadian rhythm analysis"""
        hourly_hrv = self.hrv_log.groupby(
            self.hrv_log['date'].dt.hour
        )['sdnn'].mean()
        ax.plot(hourly_hrv.index, hourly_hrv.values)
        ax.set_title('24-Hour HRV Pattern')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('SDNN (ms)')

    def _plot_stress_response(self, ax):
        """Plot stress response analysis"""
        stress_index = self.hrv_log['lf_hf_ratio'] / self.hrv_log['sdnn']
        ax.plot(self.hrv_log['date'], stress_index)
        ax.set_title('Stress Response Index')
        ax.set_ylabel('Stress Index (arbitrary units)')

    def _plot_long_term_trends(self, ax):
        """Plot long-term HRV trends"""
        monthly_trend = self.hrv_log.resample('M', on='date').mean()
        ax.plot(monthly_trend.index, monthly_trend['sdnn'], 'o-')
        ax.set_title('Monthly HRV Trend')
        ax.set_ylabel('SDNN (ms)')

    def _plot_autonomic_dashboard(self, ax):
        """Plot autonomic balance dashboard"""
        ax.scatter(self.hrv_log['lf_nu'], self.hrv_log['hf_nu'], 
                  c=self.hrv_log['lf_hf_ratio'])
        ax.set_xlabel('LF (n.u.)')
        ax.set_ylabel('HF (n.u.)')
        ax.set_title('Autonomic Balance Dashboard')

    def generate_statistical_report(self):
        """Generate comprehensive statistical report"""
        stats = self.calculate_statistics()
        
        report = {
            'Basic Statistics': {
                'SDNN': {
                    'Mean': np.mean(self.hrv_log['sdnn']),
                    'STD': np.std(self.hrv_log['sdnn']),
                    'CV': np.std(self.hrv_log['sdnn']) / np.mean(self.hrv_log['sdnn'])
                },
                'RMSSD': {
                    'Mean': np.mean(self.hrv_log['rmssd']),
                    'STD': np.std(self.hrv_log['rmssd']),
                    'CV': np.std(self.hrv_log['rmssd']) / np.mean(self.hrv_log['rmssd'])
                }
            },
            'Trend Analysis': {
                'Weekly Trend': stats['Weekly Stats'],
                'Monthly Trend': stats['Monthly Trends']
            },
            'Correlations': stats['Correlations'],
            'Variability Index': {
                'Mean': np.mean(stats['Variability Index']),
                'STD': np.std(stats['Variability Index'])
            }
        }
        
        return report

# Usage example:
def main():
    analyzer = AdvancedHRVAnalysis()
    
    # Add your data here...
    
    # Generate visualizations
    analyzer.visualize_advanced_metrics()
    
    # Generate statistical report
    report = analyzer.generate_statistical_report()
    
    # Print report
    print("\nStatistical Report:")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()