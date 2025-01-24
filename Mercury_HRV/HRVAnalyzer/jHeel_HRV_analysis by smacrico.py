"""
Unified HRV Analysis System
Combines analysis from multiple HRV data sources and provides enhanced analytics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import sqlite3
from scipy import stats
from sklearn.preprocessing import StandardScaler
import logging
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedHRVAnalysis:
    def __init__(self, db_path='e:/jheel_dev/DataBasesDev/artemis_hrv.db'):
        self.db_path = db_path
        self.hrv_data = None
        self.analysis_results = {}
        self.load_data()
        self.create_analysis_tables()

    def load_data(self) -> None:
        """Load all HRV data from hrv_sessionsFBB table"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT 
                    date,
                    sd1,
                    sd2,
                    sdnn,
                    mean_rr,
                    mean_hr,
                    hrv_rmssd,
                    pnn50,
                    vlf,
                    lf,
                    hf,
                    lf_nu,
                    hf_nu
                FROM hrv_sessionsFBB
                ORDER BY date
            """
            self.hrv_data = pd.read_sql_query(query, conn)
            
            # Convert date column to datetime
            self.hrv_data['date'] = pd.to_datetime(self.hrv_data['date'])
            
            # Calculate derived metrics
            self.calculate_derived_metrics()
            
            logger.info(f"Loaded {len(self.hrv_data)} HRV records")
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def calculate_derived_metrics(self) -> None:
        """Calculate additional HRV metrics and indices"""
        try:
            # Basic ratios
            self.hrv_data['sd2_sd1_ratio'] = self.hrv_data['sd2'] / self.hrv_data['sd1']
            self.hrv_data['lf_hf_ratio'] = self.hrv_data['lf'] / self.hrv_data['hf']
            
            # Advanced metrics
            self.hrv_data['total_power'] = self.hrv_data['vlf'] + self.hrv_data['lf'] + self.hrv_data['hf']
            self.hrv_data['normalized_rmssd'] = self.hrv_data['hrv_rmssd'] / self.hrv_data['mean_rr']
            self.hrv_data['complexity_index'] = np.log(self.hrv_data['sd2'] * self.hrv_data['sd1'])
            
            # Rolling calculations
            windows = [7, 14, 30]
            for window in windows:
                self.hrv_data[f'rmssd_{window}d_avg'] = self.hrv_data['hrv_rmssd'].rolling(window).mean()
                self.hrv_data[f'lf_hf_{window}d_avg'] = self.hrv_data['lf_hf_ratio'].rolling(window).mean()
                self.hrv_data[f'total_power_{window}d_avg'] = self.hrv_data['total_power'].rolling(window).mean()
            
            # Standardized scores
            scaler = StandardScaler()
            self.hrv_data['rmssd_zscore'] = scaler.fit_transform(self.hrv_data[['hrv_rmssd']])
            self.hrv_data['stress_index'] = scaler.fit_transform(self.hrv_data[['lf_hf_ratio']])
            
            logger.info("Calculated derived metrics successfully")
            
        except Exception as e:
            logger.error(f"Error calculating derived metrics: {e}")
            raise

    def create_analysis_tables(self) -> None:
        """Create or update tables for enhanced analysis results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Daily metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hrv_unified_daily_metrics (
                    date DATE PRIMARY KEY,
                    rmssd_score FLOAT,
                    autonomic_balance_score FLOAT,
                    stress_index FLOAT,
                    recovery_score FLOAT,
                    complexity_score FLOAT,
                    total_power_score FLOAT,
                    training_readiness FLOAT
                )
            """)
            
            # Weekly trends table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hrv_unified_weekly_trends (
                    week_start DATE PRIMARY KEY,
                    rmssd_trend FLOAT,
                    lf_hf_trend FLOAT,
                    stress_adaptation_score FLOAT,
                    training_load_score FLOAT,
                    recovery_efficiency FLOAT,
                    performance_readiness FLOAT
                )
            """)
            
            # Pattern analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hrv_unified_pattern_analysis (
                    date DATE PRIMARY KEY,
                    circadian_pattern_score FLOAT,
                    anomaly_score FLOAT,
                    pattern_consistency FLOAT,
                    adaptation_capacity FLOAT,
                    recovery_pattern_quality FLOAT
                )
            """)
            
            # Health risk indicators table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hrv_unified_health_indicators (
                    date DATE PRIMARY KEY,
                    autonomic_risk_score FLOAT,
                    stress_accumulation_index FLOAT,
                    cardiovascular_health_score FLOAT,
                    recovery_capacity FLOAT,
                    overall_health_score FLOAT
                )
            """)
            
            conn.commit()
            logger.info("Created analysis tables successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            if conn:
                conn.close()
                
                
    def calculate_health_metrics(self) -> Dict[str, pd.Series]:
            """Calculate comprehensive health and performance metrics"""
            try:
                metrics = {}
                
                # Stress Index (combines multiple stress indicators)
                metrics['stress_index'] = (
                    (self.hrv_data['sd2_sd1_ratio'] * 0.3) +
                    (self.hrv_data['lf_hf_ratio'] * 0.3) +
                    ((1 - self.hrv_data['normalized_rmssd']) * 0.4)
                )
                
                # Recovery Score
                metrics['recovery_score'] = (
                    (self.hrv_data['hrv_rmssd'] / 100) * 0.4 +
                    (1 - (metrics['stress_index'] / 10)) * 0.3 +
                    (self.hrv_data['hf_nu'] / 100) * 0.3
                ) * 100
                
                # Autonomic Balance Score
                metrics['autonomic_balance'] = (
                    (self.hrv_data['lf_nu'] / self.hrv_data['hf_nu'] - 1) * 50 + 50
                ).clip(0, 100)
                
                # Training Readiness Score
                metrics['training_readiness'] = (
                    (metrics['recovery_score'] * 0.4) +
                    ((100 - metrics['stress_index']) * 0.3) +
                    (self.hrv_data['complexity_index'] * 10 * 0.3)
                ).clip(0, 100)
                
                # Cardiovascular Health Score
                metrics['cv_health_score'] = (
                    (self.hrv_data['sdnn'] / 100 * 0.3) +
                    (self.hrv_data['total_power'] / 10000 * 0.3) +
                    (metrics['recovery_score'] / 100 * 0.4)
                ) * 100
                
                return metrics
                
            except Exception as e:
                logger.error(f"Error calculating health metrics: {e}")
                raise

    def analyze_patterns(self) -> Dict[str, pd.Series]:
        """Analyze HRV patterns and rhythms"""
        try:
            patterns = {}
            
            # Calculate health metrics first to get recovery_score
            health_metrics = self.calculate_health_metrics()
            
            # Add recovery_score to hrv_data temporarily for calculations
            self.hrv_data['recovery_score'] = health_metrics['recovery_score']
            self.hrv_data['stress_index'] = health_metrics['stress_index']
            
            # Circadian Rhythm Analysis
            daily_avg = self.hrv_data.groupby(self.hrv_data['date'].dt.hour)['hrv_rmssd'].mean()
            patterns['circadian_consistency'] = 1 - daily_avg.std() / daily_avg.mean()
            
            # Anomaly Detection
            rolling_mean = self.hrv_data['hrv_rmssd'].rolling(window=7).mean()
            rolling_std = self.hrv_data['hrv_rmssd'].rolling(window=7).std()
            patterns['anomaly_scores'] = abs(self.hrv_data['hrv_rmssd'] - rolling_mean) / rolling_std
            
            # Recovery Pattern Analysis
            patterns['recovery_consistency'] = (
                self.hrv_data['recovery_score'].diff().rolling(window=7).std() * -1 + 100
            ).clip(0, 100)
            
            # Adaptation Capacity
            stress_recovery_ratio = (
                self.hrv_data['stress_index'].rolling(window=7).mean() /
                self.hrv_data['recovery_score'].rolling(window=7).mean()
            )                                   
            patterns['adaptation_capacity'] = (1 - stress_recovery_ratio) * 100
            
            # Remove temporary columns
            self.hrv_data = self.hrv_data.drop(['recovery_score', 'stress_index'], axis=1, errors='ignore')
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            raise

    def calculate_trends(self, window: int = 7) -> Dict[str, float]:
        """Calculate trends in key metrics"""
        try:
            trends = {}
            
            # Calculate health metrics to get recovery_score
            health_metrics = self.calculate_health_metrics()
            self.hrv_data['recovery_score'] = health_metrics['recovery_score']
            
            # Define metrics to analyze
            metrics_to_analyze = ['hrv_rmssd', 'lf_hf_ratio', 'total_power', 'recovery_score']
            
            # Calculate linear trends for key metrics
            for metric in metrics_to_analyze:
                if metric in self.hrv_data.columns:
                    x = np.arange(len(self.hrv_data.tail(window)))
                    y = self.hrv_data[metric].tail(window).values
                    slope, _, _, _, _ = stats.linregress(x, y)
                    trends[f'{metric}_trend'] = slope
            
            # Create a list of trend keys before calculating relative changes
            trend_keys = list(trends.keys())
            
            # Calculate relative changes
            for metric_trend in trend_keys:
                metric_name = metric_trend.replace('_trend', '')
                baseline = self.hrv_data[metric_name].tail(window).mean()
                if baseline != 0:  # Avoid division by zero
                    trends[f'{metric_name}_relative_change'] = (trends[metric_trend] / baseline) * 100
                else:
                    trends[f'{metric_name}_relative_change'] = 0.0
            
            # Clean up temporary column
            self.hrv_data = self.hrv_data.drop('recovery_score', axis=1, errors='ignore')
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            raise
        
    
    def generate_risk_assessment(self) -> Dict[str, pd.Series]:
        """Generate health risk assessment based on HRV patterns"""
        try:
            # Calculate health metrics first to get stress_index and recovery_score
            health_metrics = self.calculate_health_metrics()
            
            # Add required metrics to hrv_data temporarily
            self.hrv_data['stress_index'] = health_metrics['stress_index']
            self.hrv_data['recovery_score'] = health_metrics['recovery_score']
            
            risk_scores = {}
            
            # Autonomic Dysfunction Risk
            risk_scores['autonomic_risk'] = (
                (1 - self.hrv_data['hrv_rmssd'].rolling(30).mean() / 100) * 0.4 +
                (self.hrv_data['lf_hf_ratio'].rolling(30).std() / 2) * 0.3 +
                (1 - self.hrv_data['total_power'].rolling(30).mean() / 10000) * 0.3
            ) * 100
            
            # Stress Accumulation Risk
            risk_scores['stress_accumulation'] = (
                self.hrv_data['stress_index'].rolling(30).mean() * 0.5 +
                (1 - self.hrv_data['recovery_score'].rolling(30).mean() / 100) * 0.5
            ) * 100
            
            # Cardiovascular Risk
            risk_scores['cardiovascular_risk'] = (
                (1 - self.hrv_data['sdnn'].rolling(30).mean() / 100) * 0.4 +
                (self.hrv_data['lf_hf_ratio'].rolling(30).mean() / 4) * 0.3 +
                (1 - self.hrv_data['total_power'].rolling(30).mean() / 10000) * 0.3
            ) * 100
            
            # Remove temporary columns
            self.hrv_data = self.hrv_data.drop(['stress_index', 'recovery_score'], axis=1, errors='ignore')
            
            return risk_scores
            
        except Exception as e:
            logger.error(f"Error generating risk assessment: {e}")
            raise

    def store_analysis_results(self) -> None:
        """Store all analysis results in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Calculate all metrics in the correct order
            health_metrics = self.calculate_health_metrics()
            patterns = self.analyze_patterns()
            risks = self.generate_risk_assessment()
            
            # Add required metrics to hrv_data temporarily
            self.hrv_data['stress_index'] = health_metrics['stress_index']
            self.hrv_data['recovery_score'] = health_metrics['recovery_score']
            
            # Prepare daily metrics
            daily_metrics = pd.DataFrame({
                'date': self.hrv_data['date'],
                'rmssd_score': self.hrv_data['hrv_rmssd'],
                'autonomic_balance_score': health_metrics['autonomic_balance'],
                'stress_index': health_metrics['stress_index'],
                'recovery_score': health_metrics['recovery_score'],
                'complexity_score': self.hrv_data['complexity_index'],
                'total_power_score': self.hrv_data['total_power'],
                'training_readiness': health_metrics['training_readiness']
            })
            
            # Prepare pattern analysis data
            pattern_analysis = pd.DataFrame({
                'date': self.hrv_data['date'],
                'circadian_pattern_score': patterns['circadian_consistency'],
                'anomaly_score': patterns['anomaly_scores'],
                'pattern_consistency': patterns['recovery_consistency'],
                'adaptation_capacity': patterns['adaptation_capacity'],
                'recovery_pattern_quality': patterns['recovery_consistency']
            })
            
            # Prepare weekly trends data
            weekly_data = self.hrv_data.set_index('date').resample('W').mean()
            weekly_trends = pd.DataFrame({
                'week_start': weekly_data.index,
                'rmssd_trend': weekly_data['hrv_rmssd'],
                'lf_hf_trend': weekly_data['lf_hf_ratio'],
                'stress_adaptation_score': 100 - weekly_data['lf_hf_ratio'],
                'training_load_score': weekly_data['total_power'],
                'recovery_efficiency': weekly_data['sdnn'],
                'performance_readiness': weekly_data['total_power'] / weekly_data['lf_hf_ratio']
            })
            
            # Prepare health indicators data
            health_indicators = pd.DataFrame({
                'date': self.hrv_data['date'],
                'autonomic_risk_score': risks['autonomic_risk'],
                'stress_accumulation_index': risks['stress_accumulation'],
                'cardiovascular_health_score': health_metrics['cv_health_score'],
                'recovery_capacity': health_metrics['recovery_score'],
                'overall_health_score': (health_metrics['cv_health_score'] + 
                                    health_metrics['recovery_score']) / 2
            })
            
            # Store in database
            daily_metrics.to_sql('hrv_unified_daily_metrics', conn, 
                            if_exists='replace', index=False)
            pattern_analysis.to_sql('hrv_unified_pattern_analysis', conn,
                                if_exists='replace', index=False)
            weekly_trends.to_sql('hrv_unified_weekly_trends', conn,
                            if_exists='replace', index=True)
            health_indicators.to_sql('hrv_unified_health_indicators', conn,
                                if_exists='replace', index=False)
            
            logger.info("Stored analysis results successfully")
            
        except Exception as e:
            logger.error(f"Error storing analysis results: {e}")
            raise
        finally:
            if conn:
                conn.close()
            # Clean up temporary columns
            self.hrv_data = self.hrv_data.drop(['stress_index', 'recovery_score'], 
                                            axis=1, errors='ignore')
                
                
    def create_visualization_dashboard(self) -> None:
            """Create comprehensive HRV analysis dashboard"""
            try:
                plt.style.use('seaborn-v0_8-darkgrid')
                fig = plt.figure(figsize=(20, 15))
                
                # Create subplots
                self._plot_time_domain(plt.subplot(331))
                self._plot_frequency_domain(plt.subplot(332))
                self._plot_stress_recovery(plt.subplot(333))
                self._plot_autonomic_balance(plt.subplot(334))
                self._plot_training_readiness(plt.subplot(335))
                self._plot_health_risks(plt.subplot(336))
                self._plot_patterns(plt.subplot(337))
                self._plot_trends(plt.subplot(338))
                self._plot_complexity(plt.subplot(339))
                
                plt.tight_layout(pad=3.0)
                fig.suptitle('Comprehensive HRV Analysis Dashboard', fontsize=16, y=1.02)
                
                plt.show()
                
            except Exception as e:
                logger.error(f"Error creating visualization dashboard: {e}")
                raise

    def _plot_time_domain(self, ax: plt.Axes) -> None:
        """Plot time domain HRV measures"""
        ax.plot(self.hrv_data['date'], self.hrv_data['hrv_rmssd'], 
                'b-', label='RMSSD', linewidth=1)
        ax.plot(self.hrv_data['date'], self.hrv_data['sdnn'], 
                'r-', label='SDNN', linewidth=1)
        ax.set_title('Time Domain Measures')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        
    def _plot_frequency_domain(self, ax: plt.Axes) -> None:
        """Plot frequency domain HRV measures"""
        ax.plot(self.hrv_data['date'], self.hrv_data['lf'], 
                'g-', label='LF', linewidth=1)
        ax.plot(self.hrv_data['date'], self.hrv_data['hf'], 
                'b-', label='HF', linewidth=1)
        ax.plot(self.hrv_data['date'], self.hrv_data['vlf'], 
                'r-', label='VLF', linewidth=1)
        ax.set_title('Frequency Domain Measures')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_stress_recovery(self, ax: plt.Axes) -> None:
        """Plot stress and recovery metrics"""
        metrics = self.calculate_health_metrics()
        ax.plot(self.hrv_data['date'], metrics['stress_index'], 
                'r-', label='Stress Index', linewidth=1)
        ax.plot(self.hrv_data['date'], metrics['recovery_score'], 
                'g-', label='Recovery Score', linewidth=1)
        ax.set_title('Stress vs Recovery Balance')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_autonomic_balance(self, ax: plt.Axes) -> None:
        """Plot autonomic balance metrics"""
        ax.plot(self.hrv_data['date'], self.hrv_data['lf_hf_ratio'], 
                'purple', label='LF/HF Ratio', linewidth=1)
        ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
        ax.set_title('Autonomic Balance')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_training_readiness(self, ax: plt.Axes) -> None:
        """Plot training readiness metrics"""
        metrics = self.calculate_health_metrics()
        ax.plot(self.hrv_data['date'], metrics['training_readiness'], 
                'b-', label='Training Readiness', linewidth=1)
        ax.set_title('Training Readiness Score')
        ax.set_ylim(0, 100)
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_health_risks(self, ax: plt.Axes) -> None:
        """Plot health risk indicators"""
        risks = self.generate_risk_assessment()
        for risk_type, scores in risks.items():
            ax.plot(self.hrv_data['date'], scores, 
                   label=risk_type.replace('_', ' ').title(), linewidth=1)
        ax.set_title('Health Risk Indicators')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_patterns(self, ax: plt.Axes) -> None:
        """Plot pattern analysis results"""
        patterns = self.analyze_patterns()
        ax.plot(self.hrv_data['date'], patterns['adaptation_capacity'], 
                'g-', label='Adaptation Capacity', linewidth=1)
        ax.plot(self.hrv_data['date'], patterns['recovery_consistency'], 
                'b-', label='Recovery Consistency', linewidth=1)
        ax.set_title('HRV Patterns')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_trends(self, ax: plt.Axes) -> None:
        """Plot trend analysis"""
        for window in [7, 14, 30]:
            ax.plot(self.hrv_data['date'], 
                   self.hrv_data[f'rmssd_{window}d_avg'], 
                   label=f'{window}-day avg', linewidth=1)
        ax.set_title('RMSSD Trends')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def _plot_complexity(self, ax: plt.Axes) -> None:
        """Plot complexity metrics"""
        ax.plot(self.hrv_data['date'], self.hrv_data['complexity_index'], 
                'b-', label='Complexity Index', linewidth=1)
        ax.set_title('HRV Complexity')
        ax.legend()
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

    def generate_summary_report(self) -> str:
        """Generate a text summary of the HRV analysis"""
        try:
            metrics = self.calculate_health_metrics()
            risks = self.generate_risk_assessment()
            trends = self.calculate_trends()
            
            latest_date = self.hrv_data['date'].max()
            
            # Get available trend metrics
            hrv_trend = trends.get('hrv_rmssd_trend', 0)
            lf_hf_trend = trends.get('lf_hf_ratio_trend', 0)
            recovery_trend = trends.get('recovery_score_trend', 0)
            
            report = f"""
    HRV Analysis Summary Report - {latest_date.strftime('%Y-%m-%d')}

    Key Metrics (latest values):
    - Recovery Score: {metrics['recovery_score'].iloc[-1]:.1f}/100
    - Training Readiness: {metrics['training_readiness'].iloc[-1]:.1f}/100
    - Autonomic Balance: {metrics['autonomic_balance'].iloc[-1]:.1f}/100
    - Stress Index: {metrics['stress_index'].iloc[-1]:.1f}/100

    Health Risk Assessment:
    - Autonomic Risk: {risks['autonomic_risk'].iloc[-1]:.1f}%
    - Cardiovascular Risk: {risks['cardiovascular_risk'].iloc[-1]:.1f}%
    - Stress Accumulation: {risks['stress_accumulation'].iloc[-1]:.1f}%

    7-Day Trends:
    - RMSSD Trend: {hrv_trend:.2f}
    - LF/HF Ratio Trend: {lf_hf_trend:.2f}
    - Recovery Score Trend: {recovery_trend:.2f}

    Recommendations:
    {self._generate_recommendations()}
    """
            return report
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise
        
        
    def _generate_recommendations(self) -> str:
        """Generate personalized recommendations based on HRV analysis"""
        metrics = self.calculate_health_metrics()
        recommendations = []
        
        # Recovery recommendations
        if metrics['recovery_score'].iloc[-1] < 60:
            recommendations.append("- Consider increasing recovery time and sleep quality")
        
        # Training recommendations
        if metrics['training_readiness'].iloc[-1] < 70:
            recommendations.append("- Reduce training intensity or take additional rest")
        
        # Stress management recommendations
        if metrics['stress_index'].iloc[-1] > 70:
            recommendations.append("- Implement stress management techniques")
        
        return "\n".join(recommendations) if recommendations else "- All metrics within optimal ranges"                

def main():
    """Main execution function"""
    try:
        # Initialize the HRV analysis system
        hrv_analyzer = UnifiedHRVAnalysis()
        logger.info("HRV Analysis System initialized successfully")

        # Store all analysis results
        hrv_analyzer.store_analysis_results()
        logger.info("Analysis results stored in database")

        # Generate and display visualizations
        hrv_analyzer.create_visualization_dashboard()
        logger.info("Created visualization dashboard")

        # Generate and print summary report
        report = hrv_analyzer.generate_summary_report()
        print("\nHRV Analysis Summary Report:")
        print(report)

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

# Example usage with additional analysis options
if __name__ == "__main__":
    # Run basic analysis
    main()

    # Example of accessing specific analyses
    try:
        analyzer = UnifiedHRVAnalysis()
        
        # Get specific date range analysis
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 15)
        date_mask = (analyzer.hrv_data['date'] >= start_date) & (analyzer.hrv_data['date'] <= end_date)
        period_data = analyzer.hrv_data[date_mask]
        
        print("\nAnalyzing specific date range:", start_date.date(), "to", end_date.date())
        
        # Calculate metrics for the period
        metrics = analyzer.calculate_health_metrics()
        risks = analyzer.generate_risk_assessment()
        
        # Print period statistics
        print("\nPeriod Statistics:")
        print(f"Average RMSSD: {period_data['hrv_rmssd'].mean():.2f}")
        print(f"Average Recovery Score: {metrics['recovery_score'][date_mask].mean():.2f}")
        print(f"Average Stress Index: {metrics['stress_index'][date_mask].mean():.2f}")
        
        # Generate weekly analysis
        weekly_stats = period_data.set_index('date').resample('W').mean()
        print("\nWeekly Trends:")
        print(weekly_stats[['hrv_rmssd', 'lf_hf_ratio', 'total_power']].round(2))
        
        # Export results to CSV
        export_filename = 'hrv_analysis_results.csv'
        combined_results = pd.DataFrame({
            'date': analyzer.hrv_data['date'],
            'rmssd': analyzer.hrv_data['hrv_rmssd'],
            'recovery_score': metrics['recovery_score'],
            'stress_index': metrics['stress_index'],
            'training_readiness': metrics['training_readiness'],
            'autonomic_balance': metrics['autonomic_balance']
        })
        combined_results.to_csv(export_filename, index=False)
        print(f"\nResults exported to {export_filename}")

    except Exception as e:
        logger.error(f"Error in example analysis: {e}")
        raise