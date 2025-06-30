import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class HRVVisualizer:
    """Comprehensive HRV visualization and trend analysis system"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        
    def get_hrv_data(self, days=30, source=None):
        """Retrieve HRV data for visualization"""
        conn = sqlite3.connect(self.db_path)
        
        where_clause = "WHERE timestamp >= date('now', ?)"
        params = [f'-{days} days']
        
        if source:
            where_clause += " AND source = ?"
            params.append(source)
            
        query = f"""
        SELECT date(timestamp) as date, 
               AVG(hrv_rmssd) as avg_rmssd, 
               AVG(sdnn) as avg_sdnn,
               AVG(hrv_pnn50) as avg_pnn50,
               AVG(mean_hr) as avg_hr,
               AVG(recovery) as avg_recovery,
               COUNT(*) as session_count,
               source
        FROM hrv_sessions
        {where_clause}
        GROUP BY date(timestamp), source
        ORDER BY date(timestamp) ASC
        """
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Database error: {e}")
            return self._generate_sample_data(days)
        finally:
            conn.close()
    
    def _generate_sample_data(self, days=30):
        """Generate sample data when database is not available"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'avg_rmssd': np.random.normal(50, 8, days) + np.sin(np.arange(days)/7) * 5,
            'avg_sdnn': np.random.normal(60, 10, days) + np.sin(np.arange(days)/7) * 7,
            'avg_pnn50': np.random.normal(25, 5, days),
            'avg_hr': np.random.normal(65, 5, days),
            'avg_recovery': np.random.normal(75, 10, days),
            'session_count': np.random.randint(1, 4, days),
            'source': ['MIXED'] * days
        })

    def create_comprehensive_dashboard(self, days=30):
        """Create a comprehensive HRV dashboard"""
        df = self.get_hrv_data(days)
        
        if df.empty:
            print("No data available for visualization")
            return
        
        # Create subplot layout
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('HRV Health Dashboard - Last 30 Days', fontsize=16, fontweight='bold')
        
        # 1. HRV Trends Over Time
        axes[0,0].plot(df['date'], df['avg_rmssd'], 'o-', label='RMSSD', linewidth=2, markersize=4)
        axes[0,0].plot(df['date'], df['avg_sdnn'], 's-', label='SDNN', linewidth=2, markersize=4)
        axes[0,0].set_title('HRV Trend Analysis', fontweight='bold')
        axes[0,0].set_ylabel('HRV Value (ms)')
        axes[0,0].legend()
        axes[0,0].tick_params(axis='x', rotation=45)
        self._add_trend_lines(axes[0,0], df['date'], df['avg_rmssd'], df['avg_sdnn'])
        
        # 2. Recovery Score Trend
        axes[0,1].plot(df['date'], df['avg_recovery'], 'o-', color='green', linewidth=2)
        axes[0,1].fill_between(df['date'], df['avg_recovery'], alpha=0.3, color='green')
        axes[0,1].axhline(y=70, color='orange', linestyle='--', label='Target Recovery')
        axes[0,1].set_title('Recovery Score Trend', fontweight='bold')
        axes[0,1].set_ylabel('Recovery Score')
        axes[0,1].legend()
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # 3. Heart Rate Variability
        axes[0,2].scatter(df['avg_hr'], df['avg_rmssd'], c=df['avg_recovery'], 
                         cmap='RdYlGn', s=60, alpha=0.7)
        axes[0,2].set_title('HR vs HRV Correlation', fontweight='bold')
        axes[0,2].set_xlabel('Average Heart Rate (bpm)')
        axes[0,2].set_ylabel('RMSSD (ms)')
        plt.colorbar(axes[0,2].collections[0], ax=axes[0,2], label='Recovery Score')
        
        # 4. Weekly Pattern Analysis
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_pattern = df.groupby('day_of_week')['avg_rmssd'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        axes[1,0].bar(weekly_pattern.index, weekly_pattern.values, color='skyblue', alpha=0.7)
        axes[1,0].set_title('Weekly HRV Pattern', fontweight='bold')
        axes[1,0].set_ylabel('Average RMSSD (ms)')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 5. Distribution Analysis
        axes[1,1].hist(df['avg_rmssd'], bins=12, alpha=0.7, color='blue', label='RMSSD')
        axes[1,1].hist(df['avg_sdnn'], bins=12, alpha=0.7, color='red', label='SDNN')
        axes[1,1].set_title('HRV Distribution', fontweight='bold')
        axes[1,1].set_xlabel('HRV Value (ms)')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].legend()
        
        # 6. Risk Assessment
        risk_data = self._calculate_risk_indicators(df)
        risk_labels = list(risk_data.keys())
        risk_values = list(risk_data.values())
        colors = ['red' if v > 0.7 else 'orange' if v > 0.4 else 'green' for v in risk_values]
        
        axes[1,2].barh(risk_labels, risk_values, color=colors, alpha=0.7)
        axes[1,2].set_title('Health Risk Indicators', fontweight='bold')
        axes[1,2].set_xlabel('Risk Level (0-1)')
        axes[1,2].set_xlim(0, 1)
        
        plt.tight_layout()
        plt.show()
        
        return fig

    def _add_trend_lines(self, ax, dates, rmssd, sdnn):
        """Add trend lines to time series plot"""
        x_numeric = np.arange(len(dates))
        
        # RMSSD trend
        rmssd_coef = np.polyfit(x_numeric, rmssd, 1)
        rmssd_trend = np.poly1d(rmssd_coef)
        ax.plot(dates, rmssd_trend(x_numeric), '--', color='blue', alpha=0.7, linewidth=1)
        
        # SDNN trend
        sdnn_coef = np.polyfit(x_numeric, sdnn, 1)
        sdnn_trend = np.poly1d(sdnn_coef)
        ax.plot(dates, sdnn_trend(x_numeric), '--', color='red', alpha=0.7, linewidth=1)

    def _calculate_risk_indicators(self, df):
        """Calculate various health risk indicators"""
        latest_week = df.tail(7)
        previous_week = df.iloc[-14:-7] if len(df) >= 14 else df.head(7)
        
        # HRV decline risk
        hrv_decline = max(0, (previous_week['avg_rmssd'].mean() - latest_week['avg_rmssd'].mean()) / 
                         previous_week['avg_rmssd'].mean()) if len(previous_week) > 0 else 0
        
        # Recovery consistency risk
        recovery_std = latest_week['avg_recovery'].std() / 100
        
        # Heart rate elevation risk
        hr_elevation = max(0, (latest_week['avg_hr'].mean() - 65) / 20)  # Baseline 65 bpm
        
        # Overall variability risk
        rmssd_cv = latest_week['avg_rmssd'].std() / latest_week['avg_rmssd'].mean()
        
        return {
            'HRV Decline': min(1.0, hrv_decline * 5),
            'Recovery Inconsistency': min(1.0, recovery_std * 2),
            'HR Elevation': min(1.0, hr_elevation),
            'HRV Instability': min(1.0, rmssd_cv * 2)
        }

    def create_interactive_dashboard(self, days=30):
        """Create an interactive Plotly dashboard"""
        df = self.get_hrv_data(days)
        
        if df.empty:
            print("No data available for interactive visualization")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['HRV Trends', 'Recovery vs HRV', 'Weekly Patterns', 'Risk Assessment'],
            specs=[[{"secondary_y": True}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # HRV Trends
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_rmssd'], name='RMSSD', 
                      line=dict(color='blue', width=3), mode='lines+markers'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_sdnn'], name='SDNN', 
                      line=dict(color='red', width=3), mode='lines+markers'),
            row=1, col=1, secondary_y=True
        )
        
        # Recovery vs HRV scatter
        fig.add_trace(
            go.Scatter(x=df['avg_rmssd'], y=df['avg_recovery'], 
                      mode='markers', name='Recovery vs RMSSD',
                      marker=dict(size=8, color=df['avg_hr'], colorscale='Viridis', 
                                showscale=True, colorbar=dict(title="Heart Rate"))),
            row=1, col=2
        )
        
        # Weekly patterns
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_pattern = df.groupby('day_of_week')['avg_rmssd'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig.add_trace(
            go.Bar(x=weekly_pattern.index, y=weekly_pattern.values, 
                   name='Weekly RMSSD', marker_color='lightblue'),
            row=2, col=1
        )
        
        # Risk assessment
        risk_data = self._calculate_risk_indicators(df)
        colors = ['red' if v > 0.7 else 'orange' if v > 0.4 else 'green' for v in risk_data.values()]
        
        fig.add_trace(
            go.Bar(y=list(risk_data.keys()), x=list(risk_data.values()), 
                   orientation='h', name='Risk Levels', marker_color=colors),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Interactive HRV Health Dashboard",
            title_x=0.5,
            height=800,
            showlegend=True
        )
        
        fig.show()
        return fig

    def generate_trend_report(self, days=30):
        """Generate a comprehensive trend analysis report"""
        df = self.get_hrv_data(days)
        
        if df.empty:
            print("No data available for trend analysis")
            return
        
        print("=" * 60)
        print("HRV TREND ANALYSIS REPORT")
        print("=" * 60)
        print(f"Analysis Period: {days} days")
        print(f"Data Points: {len(df)} sessions")
        print()
        
        # Basic statistics
        print("📊 BASIC STATISTICS")
        print("-" * 30)
        metrics = ['avg_rmssd', 'avg_sdnn', 'avg_pnn50', 'avg_hr', 'avg_recovery']
        for metric in metrics:
            if metric in df.columns:
                mean_val = df[metric].mean()
                std_val = df[metric].std()
                trend_slope = np.polyfit(range(len(df)), df[metric], 1)[0]
                print(f"{metric.replace('avg_', '').upper()}: {mean_val:.1f} ± {std_val:.1f} (trend: {trend_slope:+.3f}/day)")
        
        print()
        
        # Trend analysis
        print("📈 TREND ANALYSIS")
        print("-" * 30)
        
        # Calculate trend significance
        x = np.arange(len(df))
        for metric in ['avg_rmssd', 'avg_sdnn']:
            if metric in df.columns:
                slope, intercept = np.polyfit(x, df[metric], 1)
                correlation = np.corrcoef(x, df[metric])[0, 1]
                
                trend_strength = "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.4 else "Weak"
                trend_direction = "Improving" if slope > 0 else "Declining" if slope < 0 else "Stable"
                
                print(f"{metric.replace('avg_', '').upper()}: {trend_direction} ({trend_strength}) - {slope:+.3f}/day")
        
        print()
        
        # Risk assessment
        print("⚠️  RISK ASSESSMENT")
        print("-" * 30)
        risk_indicators = self._calculate_risk_indicators(df)
        for indicator, risk_level in risk_indicators.items():
            risk_text = "HIGH" if risk_level > 0.7 else "MODERATE" if risk_level > 0.4 else "LOW"
            print(f"{indicator}: {risk_text} ({risk_level:.2f})")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        self._generate_recommendations(df, risk_indicators)
        
        print("=" * 60)

    def _generate_recommendations(self, df, risk_indicators):
        """Generate personalized recommendations based on trends"""
        recommendations = []
        
        # HRV trend recommendations
        recent_rmssd = df['avg_rmssd'].tail(7).mean()
        overall_rmssd = df['avg_rmssd'].mean()
        
        if recent_rmssd < overall_rmssd * 0.9:
            recommendations.append("• Consider increasing rest and recovery time")
            recommendations.append("• Focus on stress management techniques")
        
        # Recovery recommendations
        if risk_indicators.get('Recovery Inconsistency', 0) > 0.5:
            recommendations.append("• Establish more consistent sleep schedule")
            recommendations.append("• Monitor environmental factors affecting recovery")
        
        # Heart rate recommendations
        if risk_indicators.get('HR Elevation', 0) > 0.5:
            recommendations.append("• Monitor for signs of overtraining or stress")
            recommendations.append("• Consider reducing training intensity temporarily")
        
        # General MS-specific recommendations
        if any(risk > 0.6 for risk in risk_indicators.values()):
            recommendations.append("• Consider consulting with your healthcare provider")
            recommendations.append("• Review medication adherence and timing")
        
        if not recommendations:
            recommendations.append("• Continue current health practices")
            recommendations.append("• Maintain consistent monitoring routine")
        
        for rec in recommendations:
            print(rec)

# Usage example
def main():
    """Main function demonstrating all visualization capabilities"""
    
    # Initialize visualizer
    visualizer = HRVVisualizer("hrv_unified.db")
    
    print("Creating comprehensive dashboard...")
    visualizer.create_comprehensive_dashboard(days=30)
    
    print("\nGenerating trend analysis report...")
    visualizer.generate_trend_report(days=30)
    
    print("\nCreating interactive dashboard...")
    # visualizer.create_interactive_dashboard(days=30)  # Uncomment for interactive plots

if __name__ == "__main__":
    main()
