"""
HRV Analytics Data Warehouse - Version 2.0
Refactored for consistency and bug fixes

Key improvements:
- Consistent parameter naming across recovery score functions
- Fixed SQL logic (= instead of IS, aligned column names)
- Added error handling and safe division helpers
- Schema validation and auto-creation
- Improved type hints and documentation
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HRVAnalytics:
    """
    HRV Analytics class for processing heart rate variability data
    with consistent recovery scoring and trend analysis.
    """
    
    def __init__(self, db_path: str = "c:/smakrykoDBs/Mercury_DWH_HRV.db"):
        """Initialize HRV Analytics with database path."""
        self.db_path = db_path
        self.recovery_constants = {
            'simple': {
                'rmssd_weight': 0.4,
                'sdnn_weight': 0.3,
                'pnn50_weight': 0.3,
                'rmssd_scale': 0.8,
                'sdnn_scale': 1.0,
                'pnn50_scale': 2.0
            },
            'comprehensive': {
                'time_domain_weight': 0.4,
                'freq_domain_weight': 0.35,
                'stress_weight': 0.25,
                'rmssd_scale': 0.8,
                'sdnn_scale': 1.0,
                'pnn50_scale': 2.0,
                'lf_scale': 100.0,
                'hf_scale': 100.0,
                'stress_scale': 10.0
            }
        }
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Ensure the database schema exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='hrv_data'
                """)
                
                if not cursor.fetchone():
                    logger.info("Creating hrv_data table...")
                    cursor.execute("""
                        CREATE TABLE hrv_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT NOT NULL,
                            name TEXT NOT NULL,
                            rmssd REAL,
                            sdnn REAL,
                            pnn50 REAL,
                            lf_power REAL,
                            hf_power REAL,
                            stress_index REAL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Schema created successfully")
                    
        except sqlite3.Error as e:
            logger.error(f"Database schema error: {e}")
    
    @staticmethod
    def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely divide two numbers, returning default if denominator is zero."""
        return numerator / denominator if denominator != 0 else default
    
    @staticmethod
    def normalize_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """Normalize score to be within specified range."""
        return max(min_val, min(max_val, score))
    
    def get_daily_hrv_dataframe(self, days_back: int = 30, source_name: str = "HRV") -> pd.DataFrame:
        """
        Retrieve daily HRV data from the database.
        
        Args:
            days_back: Number of days to look back
            source_name: Name of the HRV source device
            
        Returns:
            DataFrame with HRV data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT date, rmssd, sdnn, pnn50, lf_power, hf_power, stress_index
                    FROM hrv_data 
                    WHERE name = ? 
                    AND date >= date('now', '-{} days')
                    ORDER BY date DESC
                """.format(days_back)
                
                df = pd.read_sql_query(query, conn, params=[source_name])
                
                if df.empty:
                    logger.warning("No data found, generating sample data")
                    return self._generate_sample_trend_data(days_back)
                
                # Convert date column to datetime
                df['date'] = pd.to_datetime(df['date'])
                
                # Fill NaN values with 0
                numeric_columns = ['rmssd', 'sdnn', 'pnn50', 'lf_power', 'hf_power', 'stress_index']
                df[numeric_columns] = df[numeric_columns].fillna(0)
                
                return df
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return self._generate_sample_trend_data(days_back)
    
    def _generate_sample_trend_data(self, days: int = 30) -> pd.DataFrame:
        """Generate sample HRV data for demonstration purposes."""
        logger.info(f"Generating {days} days of sample HRV data")
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days-1),
            end=datetime.now(),
            freq='D'
        )
        
        # Generate realistic HRV values with some trends
        base_rmssd = 45
        base_sdnn = 50
        base_pnn50 = 15
        
        np.random.seed(42)  # For reproducible results
        
        data = {
            'date': dates,
            'rmssd': base_rmssd + np.random.normal(0, 8, len(dates)) + np.linspace(-5, 5, len(dates)),
            'sdnn': base_sdnn + np.random.normal(0, 10, len(dates)) + np.linspace(-3, 7, len(dates)),
            'pnn50': base_pnn50 + np.random.normal(0, 5, len(dates)) + np.linspace(-2, 3, len(dates)),
            'lf_power': 800 + np.random.normal(0, 200, len(dates)),
            'hf_power': 600 + np.random.normal(0, 150, len(dates)),
            'stress_index': 5 + np.random.normal(0, 2, len(dates))
        }
        
        # Ensure no negative values
        for col in ['rmssd', 'sdnn', 'pnn50', 'lf_power', 'hf_power']:
            data[col] = np.maximum(data[col], 1)
        
        data['stress_index'] = np.maximum(data['stress_index'], 0)
        
        return pd.DataFrame(data)
    
    def _get_personal_baselines(self, source_name: str = "HRV") -> Dict[str, float]:
        """
        Get personal baseline values from the last 90 days.
        
        Args:
            source_name: Name of the HRV source device
            
        Returns:
            Dictionary with baseline values
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        AVG(rmssd) as avg_rmssd,
                        AVG(sdnn) as avg_sdnn,
                        AVG(pnn50) as avg_pnn50,
                        AVG(lf_power) as avg_lf,
                        AVG(hf_power) as avg_hf,
                        AVG(stress_index) as avg_stress
                    FROM hrv_data 
                    WHERE name = ? 
                    AND date >= date('now', '-90 days')
                """
                
                result = pd.read_sql_query(query, conn, params=[source_name])
                
                if result.empty or result.iloc[0].isna().all():
                    logger.warning("No baseline data found, using default values")
                    return {
                        'avg_rmssd': 45.0,
                        'avg_sdnn': 50.0,
                        'avg_pnn50': 15.0,
                        'avg_lf': 800.0,
                        'avg_hf': 600.0,
                        'avg_stress': 5.0
                    }
                
                # Convert to dictionary and handle NaN values
                baselines = result.iloc[0].to_dict()
                for key, value in baselines.items():
                    if pd.isna(value):
                        baselines[key] = 0.0
                
                return baselines
                
        except sqlite3.Error as e:
            logger.error(f"Error getting baselines: {e}")
            return {
                'avg_rmssd': 45.0,
                'avg_sdnn': 50.0,
                'avg_pnn50': 15.0,
                'avg_lf': 800.0,
                'avg_hf': 600.0,
                'avg_stress': 5.0
            }
    
    def _calculate_simple_recovery_score(self, rmssd: float, sdnn: float, pnn50: float) -> float:
        """
        Calculate simple recovery score based on time-domain HRV metrics.
        
        Args:
            rmssd: Root Mean Square of Successive Differences
            sdnn: Standard Deviation of NN intervals
            pnn50: Percentage of NN50 intervals
            
        Returns:
            Recovery score (0-100)
        """
        constants = self.recovery_constants['simple']
        
        # Normalize inputs
        rmssd = rmssd or 0.0
        sdnn = sdnn or 0.0
        pnn50 = pnn50 or 0.0
        
        # Calculate component scores
        rmssd_score = (rmssd / constants['rmssd_scale']) * constants['rmssd_weight']
        sdnn_score = (sdnn / constants['sdnn_scale']) * constants['sdnn_weight']
        pnn50_score = (pnn50 / constants['pnn50_scale']) * constants['pnn50_weight']
        
        # Combined score
        raw_score = rmssd_score + sdnn_score + pnn50_score
        
        # Normalize to 0-100 scale
        return self.normalize_score(raw_score, 0, 100)
    
    def _calculate_comprehensive_recovery_score(self, rmssd: float, sdnn: float, pnn50: float,
                                              lf_power: float = 0, hf_power: float = 0,
                                              stress_index: float = 0) -> float:
        """
        Calculate comprehensive recovery score using time-domain, frequency-domain, and stress metrics.
        
        Args:
            rmssd: Root Mean Square of Successive Differences
            sdnn: Standard Deviation of NN intervals
            pnn50: Percentage of NN50 intervals
            lf_power: Low Frequency power
            hf_power: High Frequency power
            stress_index: Stress index
            
        Returns:
            Recovery score (0-100)
        """
        constants = self.recovery_constants['comprehensive']
        
        # Normalize inputs
        rmssd = rmssd or 0.0
        sdnn = sdnn or 0.0
        pnn50 = pnn50 or 0.0
        lf_power = lf_power or 0.0
        hf_power = hf_power or 0.0
        stress_index = stress_index or 0.0
        
        # Time domain component
        time_domain = (
            (rmssd / constants['rmssd_scale']) * 0.4 +
            (sdnn / constants['sdnn_scale']) * 0.35 +
            (pnn50 / constants['pnn50_scale']) * 0.25
        ) * constants['time_domain_weight']
        
        # Frequency domain component
        lf_hf_ratio = self.safe_divide(lf_power, hf_power, 1.0)
        freq_domain = (
            (lf_power / constants['lf_scale']) * 0.4 +
            (hf_power / constants['hf_scale']) * 0.4 +
            (1 / max(lf_hf_ratio, 0.1)) * 0.2  # Lower ratio is better
        ) * constants['freq_domain_weight']
        
        # Stress component (inverted - lower stress is better)
        stress_component = (
            max(0, constants['stress_scale'] - stress_index) / constants['stress_scale']
        ) * constants['stress_weight']
        
        # Combined score
        raw_score = time_domain + freq_domain + stress_component
        
        # Normalize to 0-100 scale
        return self.normalize_score(raw_score * 100, 0, 100)
    
    def _calculate_personalized_recovery_score(self, rmssd: float, sdnn: float, pnn50: float,
                                             lf_power: float = 0, hf_power: float = 0,
                                             stress_index: float = 0,
                                             source_name: str = "HRV") -> float:
        """
        Calculate personalized recovery score based on individual baselines.
        
        Args:
            rmssd: Root Mean Square of Successive Differences
            sdnn: Standard Deviation of NN intervals
            pnn50: Percentage of NN50 intervals
            lf_power: Low Frequency power
            hf_power: High Frequency power
            stress_index: Stress index
            source_name: Name of the HRV source device
            
        Returns:
            Recovery score (0-100)
        """
        # Get personal baselines
        baselines = self._get_personal_baselines(source_name)
        
        # Normalize inputs
        rmssd = rmssd or 0.0
        sdnn = sdnn or 0.0
        pnn50 = pnn50 or 0.0
        lf_power = lf_power or 0.0
        hf_power = hf_power or 0.0
        stress_index = stress_index or 0.0
        
        # Calculate relative scores (current vs personal baseline)
        rmssd_relative = self.safe_divide(rmssd, baselines['avg_rmssd'], 1.0)
        sdnn_relative = self.safe_divide(sdnn, baselines['avg_sdnn'], 1.0)
        pnn50_relative = self.safe_divide(pnn50, baselines['avg_pnn50'], 1.0)
        lf_relative = self.safe_divide(lf_power, baselines['avg_lf'], 1.0)
        hf_relative = self.safe_divide(hf_power, baselines['avg_hf'], 1.0)
        stress_relative = self.safe_divide(baselines['avg_stress'], max(stress_index, 0.1), 1.0)  # Inverted
        
        # Weighted combination
        score = (
            rmssd_relative * 0.25 +
            sdnn_relative * 0.25 +
            pnn50_relative * 0.20 +
            lf_relative * 0.10 +
            hf_relative * 0.10 +
            stress_relative * 0.10
        ) * 100
        
        # Normalize to 0-100 scale
        return self.normalize_score(score, 0, 100)
    
    def analyze_hrv_trends(self, days_back: int = 30, source_name: str = "HRV",
                          include_stats: bool = True) -> Dict[str, Any]:
        """
        Analyze HRV trends and calculate recovery scores.
        
        Args:
            days_back: Number of days to analyze
            source_name: Name of the HRV source device
            include_stats: Whether to include detailed statistics
            
        Returns:
            Dictionary with trend analysis results
        """
        # Get data
        df = self.get_daily_hrv_dataframe(days_back, source_name)
        
        if df.empty:
            return {"error": "No data available for analysis"}
        
        # Calculate recovery scores for each method
        df['simple_recovery'] = df.apply(
            lambda row: self._calculate_simple_recovery_score(
                row['rmssd'], row['sdnn'], row['pnn50']
            ), axis=1
        )
        
        df['comprehensive_recovery'] = df.apply(
            lambda row: self._calculate_comprehensive_recovery_score(
                row['rmssd'], row['sdnn'], row['pnn50'],
                row['lf_power'], row['hf_power'], row['stress_index']
            ), axis=1
        )
        
        df['personalized_recovery'] = df.apply(
            lambda row: self._calculate_personalized_recovery_score(
                row['rmssd'], row['sdnn'], row['pnn50'],
                row['lf_power'], row['hf_power'], row['stress_index'],
                source_name
            ), axis=1
        )
        
        # Basic trend analysis
        result = {
            'data_points': len(df),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            },
            'current_values': {
                'rmssd': float(df.iloc[0]['rmssd']),
                'sdnn': float(df.iloc[0]['sdnn']),
                'pnn50': float(df.iloc[0]['pnn50'])
            },
            'recovery_scores': {
                'simple': float(df.iloc[0]['simple_recovery']),
                'comprehensive': float(df.iloc[0]['comprehensive_recovery']),
                'personalized': float(df.iloc[0]['personalized_recovery'])
            },
            'dataframe': df
        }
        
        if include_stats and len(df) > 1:
            result['statistics'] = self._calculate_trend_statistics(df)
        
        return result
    
    def _calculate_trend_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate detailed trend statistics."""
        stats = {}
        
        # Calculate correlations and trends for key metrics
        metrics = ['rmssd', 'sdnn', 'pnn50', 'simple_recovery', 'comprehensive_recovery', 'personalized_recovery']
        
        # Create day index for correlation
        df_copy = df.copy()
        df_copy['day_index'] = range(len(df_copy))
        
        for metric in metrics:
            if metric in df_copy.columns:
                correlation = df_copy['day_index'].corr(df_copy[metric])
                
                # Interpret correlation strength
                if abs(correlation) >= 0.7:
                    strength = "strong"
                elif abs(correlation) >= 0.3:
                    strength = "moderate"
                else:
                    strength = "weak"
                
                direction = "improving" if correlation > 0 else "declining" if correlation < 0 else "stable"
                
                stats[metric] = {
                    'correlation': float(correlation) if not pd.isna(correlation) else 0.0,
                    'trend_direction': direction,
                    'trend_strength': strength,
                    'mean': float(df_copy[metric].mean()),
                    'std': float(df_copy[metric].std()),
                    'min': float(df_copy[metric].min()),
                    'max': float(df_copy[metric].max())
                }
        
        return stats
    
    def plot_hrv_trend(self, df: pd.DataFrame, title: str = "HRV Trends") -> None:
        """
        Plot HRV trends over time.
        
        Args:
            df: DataFrame with HRV data
            title: Plot title
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(title, fontsize=16)
            
            # Time domain metrics
            axes[0, 0].plot(df['date'], df['rmssd'], 'b-', label='RMSSD', marker='o')
            axes[0, 0].plot(df['date'], df['sdnn'], 'r-', label='SDNN', marker='s')
            axes[0, 0].set_title('Time Domain Metrics')
            axes[0, 0].set_ylabel('ms')
            axes[0, 0].legend()
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Recovery scores
            axes[0, 1].plot(df['date'], df['simple_recovery'], 'g-', label='Simple', marker='o')
            axes[0, 1].plot(df['date'], df['comprehensive_recovery'], 'b-', label='Comprehensive', marker='s')
            axes[0, 1].plot(df['date'], df['personalized_recovery'], 'r-', label='Personalized', marker='^')
            axes[0, 1].set_title('Recovery Scores')
            axes[0, 1].set_ylabel('Score (0-100)')
            axes[0, 1].legend()
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Frequency domain (if available)
            if 'lf_power' in df.columns and 'hf_power' in df.columns:
                axes[1, 0].plot(df['date'], df['lf_power'], 'orange', label='LF Power', marker='o')
                axes[1, 0].plot(df['date'], df['hf_power'], 'purple', label='HF Power', marker='s')
                axes[1, 0].set_title('Frequency Domain')
                axes[1, 0].set_ylabel('ms²')
                axes[1, 0].legend()
                axes[1, 0].tick_params(axis='x', rotation=45)
            
            # PNN50 and Stress
            axes[1, 1].plot(df['date'], df['pnn50'], 'brown', label='pNN50', marker='o')
            if 'stress_index' in df.columns:
                ax2 = axes[1, 1].twinx()
                ax2.plot(df['date'], df['stress_index'], 'red', label='Stress Index', marker='s', alpha=0.7)
                ax2.set_ylabel('Stress Index', color='red')
                ax2.legend(loc='upper right')
            
            axes[1, 1].set_title('pNN50 & Stress')
            axes[1, 1].set_ylabel('pNN50 (%)', color='brown')
            axes[1, 1].legend(loc='upper left')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting HRV trends: {e}")
            print(f"Could not create trend plot: {e}")
    
    def plot_hrv_histogram(self, df: pd.DataFrame, title: str = "HRV Distribution") -> None:
        """
        Plot histograms of HRV metrics.
        
        Args:
            df: DataFrame with HRV data
            title: Plot title
        """
        try:
            fig, axes = plt.subplots(2, 3, figsize=(15, 8))
            fig.suptitle(title, fontsize=16)
            
            metrics = [
                ('rmssd', 'RMSSD (ms)', 'blue'),
                ('sdnn', 'SDNN (ms)', 'red'),
                ('pnn50', 'pNN50 (%)', 'green'),
                ('simple_recovery', 'Simple Recovery', 'orange'),
                ('comprehensive_recovery', 'Comprehensive Recovery', 'purple'),
                ('personalized_recovery', 'Personalized Recovery', 'brown')
            ]
            
            for i, (metric, label, color) in enumerate(metrics):
                row, col = divmod(i, 3)
                if metric in df.columns:
                    axes[row, col].hist(df[metric], bins=15, alpha=0.7, color=color, edgecolor='black')
                    axes[row, col].set_title(label)
                    axes[row, col].set_xlabel('Value')
                    axes[row, col].set_ylabel('Frequency')
                    
                    # Add mean line
                    mean_val = df[metric].mean()
                    axes[row, col].axvline(mean_val, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_val:.1f}')
                    axes[row, col].legend()
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error plotting HRV histogram: {e}")
            print(f"Could not create histogram: {e}")


def main():
    """Demonstration of HRV Analytics functionality."""
    print("=== HRV Analytics Demo ===")
    
    # Initialize analytics
    hrv = HRVAnalytics("c:/smakrykoDBs/Mercury_DWH_HRV.db")
    
    # Analyze trends
    print("\n1. Analyzing HRV trends...")
    results = hrv.analyze_hrv_trends(days_back=30, include_stats=True)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    print(f"Data points: {results['data_points']}")
    print(f"Date range: {results['date_range']['start']} to {results['date_range']['end']}")
    
    print("\nCurrent HRV values:")
    for metric, value in results['current_values'].items():
        print(f"  {metric.upper()}: {value:.1f}")
    
    print("\nRecovery Scores:")
    for method, score in results['recovery_scores'].items():
        print(f"  {method.capitalize()}: {score:.1f}/100")
    
    if 'statistics' in results:
        print("\nTrend Analysis:")
        for metric, stats in results['statistics'].items():
            if 'recovery' in metric:
                print(f"  {metric.replace('_', ' ').title()}: {stats['trend_direction']} ({stats['trend_strength']})")
    
    # Create visualizations
    print("\n2. Creating visualizations...")
    df = results['dataframe']
    
    hrv.plot_hrv_trend(df, "HRV Trends - Last 30 Days")
    hrv.plot_hrv_histogram(df, "HRV Metrics Distribution")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()
