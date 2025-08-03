import sqlite3
import pandas as pd
import numpy as np
import logging
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
DB_PATH = "c:/smakryko/myHealthData/DataBasesDev/Mercury_DWH-HRV.db"

# Setup logging
logger = logging.getLogger(__name__)

class HRVAnalytics:
    """Enhanced HRV Analytics and Recovery Score System"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._validate_database()
    
    def _validate_database(self):
        """Validate database connection and tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hrv_sessions'")
                if not cursor.fetchone():
                    logger.warning("hrv_sessions table not found. Creating tables...")
                    self._create_tables_if_missing()
        except sqlite3.Error as e:
            logger.error(f"Database validation failed: {e}")
            raise
    
    def _create_tables_if_missing(self):
        """Create tables if they don't exist"""
        # Implementation would go here if needed
        pass
    
    def analyze_hrv_trends(self, days: int = 30, include_stats: bool = True) -> Dict:
        """
        Enhanced HRV trend analysis with statistical significance
        
        Args:
            days: Number of days to analyze
            include_stats: Include statistical analysis
            
        Returns:
            Dictionary containing trend analysis results
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
              SELECT 
                date(timestamp) as date, 
                AVG(armssd) as avg_rmssd, 
                AVG(asdnn) as avg_sdnn,
                AVG(nn50) as avg_pnn50,
                AVG(mean_hr) as avg_hr,
                AVG(recovery) as avg_recovery,
                COUNT(*) as session_count,
                MIN(armssd) as min_rmssd,
                MAX(armssd) as max_rmssd
            FROM hrv_sessions
            WHERE timestamp >= date('now', ?) and name is 'F3b Monitor+HRV'              
            GROUP BY date(timestamp)
            ORDER BY date(timestamp) ASC

                """
                
                df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
                df['std_rmssd'] = df['avg_rmssd'].rolling(window=7).std()  # 7-day rolling std, or
                # df['std_rmssd'] = df['avg_rmssd'].std()  # overall std
 
        except sqlite3.Error as e:
            logger.error(f"Database error in analyze_hrv_trends: {e}")
            return self._generate_sample_trend_data(days)
        
        if df.empty:
            logger.warning("No HRV data found for trend analysis")
            return {"status": "no_data", "message": "No HRV data found for analysis"}
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate trends
        results = {
            "status": "success",
            "data_points": len(df),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d'),
                "end": df['date'].max().strftime('%Y-%m-%d')
            },
            "dataframe": df
        }
        
        if len(df) > 1:
            # Calculate trend statistics
            x = np.arange(len(df))
            
            # RMSSD trend
            rmssd_trend = np.polyfit(x, df['avg_rmssd'].fillna(0), 1)
            print(f"RMSSD Trend: {rmssd_trend}")
            rmssd_r_value = np.corrcoef(x, df['avg_rmssd'].fillna(0))[0, 1]
            print(f"RMSSD Correlation: {rmssd_r_value:.3f}")
            
            # SDNN trend
            sdnn_trend = np.polyfit(x, df['avg_sdnn'].fillna(0), 1)
            print(f"SDNN Trend: {sdnn_trend}")
            sdnn_r_value = np.corrcoef(x, df['avg_sdnn'].fillna(0))[0, 1]
            print(f"SDNN Correlation: {sdnn_r_value:.3f}")
            
            results.update({
                "trends": {
                    "rmssd": {
                        "slope": rmssd_trend[0],
                        "intercept": rmssd_trend[1],
                        "correlation": rmssd_r_value,
                        "trend_strength": self._interpret_trend_strength(abs(rmssd_r_value)),
                        "direction": "improving" if rmssd_trend[0] > 0 else "declining" if rmssd_trend[0] < 0 else "stable"
                    },
                    "sdnn": {
                        "slope": sdnn_trend[0],
                        "intercept": sdnn_trend[1],
                        "correlation": sdnn_r_value,
                        "trend_strength": self._interpret_trend_strength(abs(sdnn_r_value)),
                        "direction": "improving" if sdnn_trend[0] > 0 else "declining" if sdnn_trend[0] < 0 else "stable"
                    }
                }
            })
            
            if include_stats:
                results["statistics"] = self._calculate_trend_statistics(df)
        
        # Print summary
        self._print_trend_summary(results)
        
        return results
    
    def _interpret_trend_strength(self, correlation: float) -> str:
        """Interpret correlation strength"""
        if correlation >= 0.7:
            return "strong"
        elif correlation >= 0.4:
            return "moderate"
        elif correlation >= 0.2:
            return "weak"
        else:
            return "negligible"
    
    def _calculate_trend_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive trend statistics"""
        return {
            "rmssd": {
                "mean": df['avg_rmssd'].mean(),
                "std": df['avg_rmssd'].std(),
                "min": df['avg_rmssd'].min(),
                "max": df['avg_rmssd'].max(),
                "cv": (df['avg_rmssd'].std() / df['avg_rmssd'].mean()) * 100,  # Coefficient of variation
                "recent_7day_avg": df['avg_rmssd'].tail(7).mean(),
                "recent_vs_overall": ((df['avg_rmssd'].tail(7).mean() / df['avg_rmssd'].mean()) - 1) * 100
            },
            "sdnn": {
                "mean": df['avg_sdnn'].mean(),
                "std": df['avg_sdnn'].std(),
                "min": df['avg_sdnn'].min(),
                "max": df['avg_sdnn'].max(),
                "cv": (df['avg_sdnn'].std() / df['avg_sdnn'].mean()) * 100,
                "recent_7day_avg": df['avg_sdnn'].tail(7).mean(),
                "recent_vs_overall": ((df['avg_sdnn'].tail(7).mean() / df['avg_sdnn'].mean()) - 1) * 100
            }
        }
    
    def _print_trend_summary(self, results: Dict):
        """Print formatted trend summary"""
        if results["status"] != "success":
            print(f"Trend Analysis: {results.get('message', 'Unknown error')}")
            return
        
        print("\n" + "="*60)
        print("HRV TREND ANALYSIS REPORT")
        print("="*60)
        print(f"Analysis Period: {results['date_range']['start']} to {results['date_range']['end']}")
        print(f"Data Points: {results['data_points']} days")
        
        if "trends" in results:
            # print("\n📈 TREND SUMMARY:")
            print("\n[Trend] TREND SUMMARY:")

            print("-" * 30)
            
            rmssd_trend = results["trends"]["rmssd"]
            print(f"RMSSD: {rmssd_trend['direction'].upper()} ({rmssd_trend['trend_strength']})")
            print(f"  Slope: {rmssd_trend['slope']:+.3f} ms/day")
            print(f"  Correlation: {rmssd_trend['correlation']:.3f}")
            
            sdnn_trend = results["trends"]["sdnn"]
            print(f"SDNN: {sdnn_trend['direction'].upper()} ({sdnn_trend['trend_strength']})")
            print(f"  Slope: {sdnn_trend['slope']:+.3f} ms/day")
            print(f"  Correlation: {sdnn_trend['correlation']:.3f}")
            
        if "statistics" in results:
            stats = results["statistics"]
            # print(f"\n📊 RECENT vs OVERALL:")
            print("\n[Trend] TREND OVERALL:")

            print("-" * 30)
            print(f"RMSSD: {stats['rmssd']['recent_vs_overall']:+.1f}% change")
            print(f"SDNN: {stats['sdnn']['recent_vs_overall']:+.1f}% change")
        
        print("="*60)
    
    def calculate_recovery_score(self, activity_id: str, method: str = "comprehensive") -> Optional[Dict]:
        """
        Enhanced recovery score calculation with multiple methods
        
        Args:
            activity_id: Session identifier
            method: 'simple', 'comprehensive', or 'personalized'
            
        Returns:
            Dictionary containing recovery score and components
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT armssd, asdnn, nn50, mean_hr, recovery, 
                           lf, hf, vlf, stress_hrpa, name, source
                    FROM hrv_sessions 
                    WHERE activity_id = ?
                """, (activity_id,))
                result = cursor.fetchone()
                
        except sqlite3.Error as e:
            logger.error(f"Database error in calculate_recovery_score: {e}")
            return None
        
        if not result:
            logger.warning(f"No session data found for activity_id: {activity_id}")
            return None
        
        # Unpack results
        armssd, asdnn, nn50, mean_hr, existing_recovery, lf, hf, vlf, stress, name, source = result
        
        # Calculate based on method
        if method == "simple":
            return self._calculate_simple_recovery_score(armssd, asdnn, nn50, activity_id, name)
        elif method == "comprehensive":
            return self._calculate_comprehensive_recovery_score(
                armssd, asdnn, nn50, mean_hr, lf, hf, stress, activity_id, name
            )
        elif method == "personalized":
            return self._calculate_personalized_recovery_score(
                armssd, asdnn, nn50, mean_hr, lf, hf, stress, activity_id, name, source
            )
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_simple_recovery_score(self, armssd: float, asdnn: float, nn50: float, 
                                       activity_id: str, name: str) -> Dict:
        """Simple recovery score calculation (fixed version of original)"""
        # Handle None values
        rmssd = armssd or 0
        sdnn = asdnn or 0
        pnn50 = nn50 or 0
        
        # Fixed calculation (was dividing tuple by number)
        rmssd_score = min(100, max(0, rmssd / 0.8))  # Scale: good RMSSD ~80ms = 100 points
        sdnn_score = min(100, max(0, sdnn / 1.0))    # Scale: good SDNN ~100ms = 100 points
        pnn50_score = min(100, max(0, pnn50 * 2))    # Scale: good pNN50 ~50% = 100 points
        
        recovery_score = (rmssd_score + sdnn_score + pnn50_score) / 3
        
        result = {
            "activity_id": activity_id,
            "name": name,
            "method": "simple",
            "recovery_score": recovery_score,
            "components": {
                "rmssd_score": rmssd_score,
                "sdnn_score": sdnn_score,
                "pnn50_score": pnn50_score
            },
            "raw_values": {
                "rmssd": rmssd,
                "sdnn": sdnn,
                "pnn50": pnn50
            }
        }
        
        print(f"Simple Recovery Score for {activity_id} ({name}): {recovery_score:.1f}/100")
        return result
    
    def _calculate_comprehensive_recovery_score(self, armssd: float, asdnn: float, nn50: float,
                                              mean_hr: float, lf: float, hf: float, stress: float,
                                              activity_id: str, name: str) -> Dict:
        """Comprehensive recovery score using multiple HRV domains"""
        # Handle None values
        rmssd = rmssd or 0
        sdnn = sdnn or 0
        pnn50 = pnn50 or 0
        mean_hr = mean_hr or 65  # Default resting HR
        lf = lf or 0
        hf = hf or 0
        stress = stress or 50  # Default moderate stress
        
        # Time domain score (40% weight)
        time_domain_score = (
            min(100, max(0, rmssd / 0.8)) * 0.6 +  # RMSSD primary indicator
            min(100, max(0, sdnn / 1.0)) * 0.4     # SDNN secondary
        )
        
        # Frequency domain score (30% weight)
        if hf > 0:
            lf_hf_ratio = lf / hf
            freq_domain_score = (
                min(100, max(0, np.log10(max(1, hf)) * 25)) * 0.7 +  # HF power
                min(100, max(0, 100 - lf_hf_ratio * 20)) * 0.3       # LF/HF ratio (lower is better)
            )
        else:
            freq_domain_score = 50  # Default if no frequency data
        
        # Heart rate score (20% weight)
        hr_score = min(100, max(0, 100 - abs(mean_hr - 60) * 2))  # Optimal around 60 bpm
        
        # Stress score (10% weight)
        stress_score = min(100, max(0, 100 - stress))  # Lower stress = higher score
        
        # Weighted final score
        recovery_score = (
            time_domain_score * 0.4 +
            freq_domain_score * 0.3 +
            hr_score * 0.2 +
            stress_score * 0.1
        )
        
        result = {
            "activity_id": activity_id,
            "name": name,
            "method": "comprehensive",
            "recovery_score": recovery_score,
            "components": {
                "time_domain_score": time_domain_score,
                "freq_domain_score": freq_domain_score,
                "hr_score": hr_score,
                "stress_score": stress_score
            },
            "raw_values": {
                "rmssd": rmssd,
                "sdnn": sdnn,
                "pnn50": pnn50,
                "mean_hr": mean_hr,
                "lf": lf,
                "hf": hf,
                "stress": stress
            }
        }
        
        print(f"Comprehensive Recovery Score for {activity_id} ({name}): {recovery_score:.1f}/100")
        return result
    
    def _calculate_personalized_recovery_score(self, armssd: float, asdnn: float, pnn50: float,
                                             mean_hr: float, lf: float, hf: float, stress: float,
                                             activity_id: str, name: str, source: str) -> Dict:
        """Personalized recovery score using individual baselines"""
        # Get personal baselines (this would be implemented based on historical data)
        baselines = self._get_personal_baselines(source)
        
        # Calculate relative scores against personal baselines
        rmssd_relative = (armssd / baselines['rmssd']) * 100 if baselines['rmssd'] > 0 else 50
        sdnn_relative = (asdnn / baselines['sdnn']) * 100 if baselines['sdnn'] > 0 else 50
        
        # Apply personalized weights (could be learned from user data)
        recovery_score = min(100, max(0, (rmssd_relative + sdnn_relative) / 2))
        
        result = {
            "activity_id": activity_id,
            "name": name,
            "method": "personalized",
            "recovery_score": recovery_score,
            "baselines_used": baselines,
            "relative_scores": {
                "rmssd_relative": rmssd_relative,
                "sdnn_relative": sdnn_relative
            }
        }
        
        print(f"Personalized Recovery Score for {activity_id} ({name}): {recovery_score:.1f}/100")
        return result
    
    def _get_personal_baselines(self, source: str) -> Dict:
        """Get personal baselines for recovery score calculation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(hrv_rmssd), AVG(sdnn)
                    FROM hrv_sessions 
                    WHERE source = ? AND hrv_rmssd IS NOT NULL AND sdnn IS NOT NULL
                    AND timestamp >= date('now', '-90 days')
                """, (source,))
                result = cursor.fetchone()
                
                if result and result[0] and result[1]:
                    return {"rmssd": result[0], "sdnn": result[1]}
                
        except sqlite3.Error as e:
            logger.error(f"Error getting personal baselines: {e}")
        
        # Default baselines if no personal data available
        return {"rmssd": 45.0, "sdnn": 50.0}
    
    def _generate_sample_trend_data(self, days: int) -> Dict:
        """Generate sample data when database is not accessible"""
        logger.info("Generating sample trend data for demonstration")
        
        dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
        np.random.seed(42)
        
        df = pd.DataFrame({
            'date': dates,
            'avg_rmssd': np.random.normal(50, 8, days) + np.sin(np.arange(days)/7) * 5,
            'avg_sdnn': np.random.normal(60, 10, days) + np.sin(np.arange(days)/7) * 7,
            'avg_pnn50': np.random.normal(25, 5, days),
            'avg_hr': np.random.normal(65, 5, days),
            'avg_recovery': np.random.normal(75, 10, days),
            'session_count': np.random.randint(1, 4, days)
        })
        
        return {
            "status": "sample_data",
            "message": "Using sample data (database not accessible)",
            "dataframe": df,
            "data_points": len(df)
            
            
 
    
    
        }

def plot_hrv_trend(df):
    plt.figure()
    plt.plot(df['date'], df['daily_rmssd'])
    plt.title('HRV Trend')

def plot_hrv_histogram(df, column='daily_rmssd'):
    plt.figure()
    plt.hist(df[column])
    plt.title('HRV Histogram')
# --- Data Preparation for Visualization ---
def get_daily_hrv_dataframe(days=30):
    conn = sqlite3.connect(DB_PATH)
    print(f"Fetching daily HRV data for the last {days} days...")
    query = """
    SELECT date(timestamp) as date, AVG(armssd) as daily_rmssd
    FROM hrv_sessions
    WHERE timestamp >= date('now', ?) and name is 'F3b Monitor+HRV'
    GROUP BY date(timestamp)
    ORDER BY date(timestamp) ASC
    """
    print
    df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
    conn.close()
    return df


# === USAGE EXAMPLES ===

def main():
    """Example usage of enhanced HRV analytics"""
    
    # Initialize analytics system
    hrv_analytics = HRVAnalytics()
    
    # Plot HRV trend and histogram
    print('Plotting HRV trend and histogram...')
    df_plot = get_daily_hrv_dataframe(days=30)
    plot_hrv_trend(df_plot)
    plot_hrv_histogram(df_plot, column='daily_rmssd')
    
    
    # Example 1: Analyze trends
    print("=== HRV TREND ANALYSIS ===")
    trend_results = hrv_analytics.analyze_hrv_trends(days=30, include_stats=True)
    
    # Example 2: Calculate recovery scores
    print("\n=== RECOVERY SCORE CALCULATIONS ===")
    
    # Simple method
    simple_score = hrv_analytics.calculate_recovery_score("17080654324", method="simple")
    
    # Comprehensive method
    comprehensive_score = hrv_analytics.calculate_recovery_score("example_session_001", method="comprehensive")
    
    # Personalized method
    personalized_score = hrv_analytics.calculate_recovery_score("example_session_001", method="personalized")

if __name__ == "__main__":
    main()
